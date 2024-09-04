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
