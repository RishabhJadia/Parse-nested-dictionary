def process_row(row):
    jobmask_name = row['Name']
    instance_names = row['instance'].split(',')
    seal_name = row['seal']

    # Bulk fetch existing jobmask, instances, and seal
    jobmask = Jobmask.objects.filter(name=jobmask_name).prefetch_related('instance').first()
    instances = Instance.objects.filter(name__in=instance_names)
    seal = Seal.objects.filter(name=seal_name).first() if seal_name else None

    if jobmask:
        # Update the seal field only if necessary
        if seal_name:
            if jobmask.seal != seal:
                if not seal:
                    seal = Seal.objects.create(name=seal_name)
                jobmask.seal = seal
        else:
            if jobmask.seal is not None:
                jobmask.seal = None

        # Add new instances that are not already associated with the jobmask
        current_instances = jobmask.instance.all()
        current_instance_names = set(current_instances.values_list('name', flat=True))
        new_instance_names = set(instance_names)

        # Add missing instances
        instances_to_add = instances.exclude(name__in=current_instance_names)
        if instances_to_add:
            jobmask.instance.add(*instances_to_add)
            print(f"Added instances {', '.join(instances_to_add.values_list('name', flat=True))} to jobmask '{jobmask_name}'.")

        # Remove instances that are no longer in the CSV
        instances_to_remove = current_instances.exclude(name__in=new_instance_names)
        if instances_to_remove:
            jobmask.instance.remove(*instances_to_remove)
            print(f"Removed instances {', '.join(instances_to_remove.values_list('name', flat=True))} from jobmask '{jobmask_name}'.")

        jobmask.save(update_fields=['seal'])
        print(f"Updated jobmask '{jobmask_name}'.")
    else:
        # Create a new jobmask and related objects if needed
        if not instances.exists():
            instances = [Instance.objects.create(name=name) for name in instance_names]
            print(f"Created instances {', '.join(instance_names)}.")

        if not seal and seal_name:
            seal = Seal.objects.create(name=seal_name)

        jobmask = Jobmask.objects.create(name=jobmask_name, seal=seal)
        jobmask.instance.add(*instances)
        jobmask.save()
        print(f"Created jobmask '{jobmask_name}'.") 

-------------------------------
       
from collections import defaultdict

def process_rows(rows):
    jobmask_names = {row['Name'] for row in rows}
    instance_names = {name for row in rows for name in row['instance'].split(',')}
    seal_names = {row['seal'] for row in rows if row['seal']}

    # Fetch all relevant jobmasks, instances, and seals at once
    jobmasks = Jobmask.objects.filter(name__in=jobmask_names).prefetch_related('instance').in_bulk(field_name='name')
    instances = Instance.objects.filter(name__in=instance_names).in_bulk(field_name='name')
    seals = Seal.objects.filter(name__in=seal_names).in_bulk(field_name='name')

    new_instances = []
    new_seals = []
    jobmask_updates = []
    instance_jobmask_mapping = defaultdict(list)

    for row in rows:
        jobmask_name = row['Name']
        instance_names = row['instance'].split(',')
        seal_name = row['seal']

        jobmask = jobmasks.get(jobmask_name)

        if jobmask:
            if seal_name:
                seal = seals.get(seal_name) or Seal(name=seal_name)
                if seal_name not in seals:
                    new_seals.append(seal)
                jobmask.seal = seal

            current_instance_names = set(jobmask.instance.values_list('name', flat=True))
            new_instance_names = set(instance_names)

            # Add missing instances
            for name in new_instance_names - current_instance_names:
                instance = instances.get(name) or Instance(name=name)
                if name not in instances:
                    new_instances.append(instance)
                instance_jobmask_mapping[jobmask_name].append(instance)

            # Remove instances no longer present in the CSV
            instances_to_remove = current_instance_names - new_instance_names
            if instances_to_remove:
                jobmask.instance.remove(*instances.filter(name__in=instances_to_remove))

            jobmask_updates.append(jobmask)
        else:
            # Create a new jobmask
            seal = seals.get(seal_name) or (Seal(name=seal_name) if seal_name else None)
            if seal and seal_name not in seals:
                new_seals.append(seal)

            new_jobmask = Jobmask(name=jobmask_name, seal=seal)
            jobmasks[jobmask_name] = new_jobmask
            jobmask_updates.append(new_jobmask)

            for name in instance_names:
                instance = instances.get(name) or Instance(name=name)
                if name not in instances:
                    new_instances.append(instance)
                instance_jobmask_mapping[jobmask_name].append(instance)

    # Bulk create new instances and seals
    if new_instances:
        Instance.objects.bulk_create(new_instances)
        instances.update({instance.name: instance for instance in new_instances})
    if new_seals:
        Seal.objects.bulk_create(new_seals)
        seals.update({seal.name: seal for seal in new_seals})

    # Bulk update jobmasks and add instances in bulk
    Jobmask.objects.bulk_update(jobmask_updates, fields=['seal'])
    for jobmask_name, inst_list in instance_jobmask_mapping.items():
        jobmasks[jobmask_name].instance.add(*inst_list)
