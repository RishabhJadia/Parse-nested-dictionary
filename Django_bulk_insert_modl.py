from django_bulk_load import bulk_insert_models, bulk_update_models
from myapp.models import Job, Machine, JobMask, Instance, JobMachineMapping
import pandas as pd

# Step 1: Load existing data
def load_existing_data():
    jobs = {job.name: job for job in Job.objects.all()}
    machines = {machine.name: machine for machine in Machine.objects.all()}
    job_masks = {mask.name: mask for mask in JobMask.objects.all()}
    instances = {instance.name: instance for instance in Instance.objects.all()}
    return jobs, job_masks, instances, machines

# Function to split DataFrame into chunks
def split_dataframe(df, chunk_size):
    for start in range(0, len(df), chunk_size):
        yield df[start:start + chunk_size]

# Function to handle bulk inserts with a batch size limit
def bulk_insert_in_batches(models, batch_size=10000):
    for start in range(0, len(models), batch_size):
        bulk_insert_models(models[start:start + batch_size], ignore_conflicts=True, return_models=True)

# Step 2: Handle jobs creation and updates using bulk_insert_models and bulk_update_models
def handle_jobs(df, job_masks, instances, batch_size=10000):
    jobs_to_create = []
    jobs_to_update = []

    for _, row in df.iterrows():
        job_name = row['job_name']
        job_mask_name = row['job_mask']
        instance_name = row['instance']

        if job_name not in jobs:
            # If job doesn't exist, create it
            job = Job(
                name=job_name,
                job_mask=job_masks[job_mask_name],
                instance=instances[instance_name]
            )
            jobs_to_create.append(job)
        else:
            # If job exists, check if it needs to be updated
            job = jobs[job_name]
            if job.job_mask.name != job_mask_name or job.instance.name != instance_name:
                job.job_mask = job_masks[job_mask_name]
                job.instance = instances[instance_name]
                jobs_to_update.append(job)

    # Bulk create jobs in batches
    bulk_insert_in_batches(jobs_to_create, batch_size=batch_size)

    # Bulk update jobs (efficiently using bulk_update_models)
    if jobs_to_update:
        bulk_update_models(
            models=jobs_to_update, 
            update_field_names=['job_mask', 'instance'],
            pk_field_names=['id'],
            return_models=False  # No need to return models if not required
        )

# Step 3: Handle machines in bulk
def handle_machines(df, jobs, instances, batch_size=10000):
    machines_to_create = []
    for _, row in df.iterrows():
        machine_name = row['machine_name']
        if machine_name not in machines:
            machine = Machine(
                name=machine_name,
                node_name=row['node_name'],
                instance=instances[row['instance']],
                machine_type=row['machine_type']
            )
            machines_to_create.append(machine)

    # Bulk create machines in batches
    bulk_insert_in_batches(machines_to_create, batch_size=batch_size)

# Step 4: Handle Job-Machine mappings using bulk_insert_models
def handle_job_machine_mappings(df, jobs, machines, existing_mappings, batch_size=10000):
    job_machine_mappings = []

    for _, row in df.iterrows():
        job = jobs[row['job_name']]
        machine = machines[row['machine_name']]

        if (job.id, machine.id) not in existing_mappings:
            job_machine_mappings.append(JobMachineMapping(job=job, machine=machine))
            existing_mappings.add((job.id, machine.id))  # Update existing mappings set

    # Bulk insert job-machine mappings in batches
    bulk_insert_in_batches(job_machine_mappings, batch_size=batch_size)

# Step 5: Process the CSV in bulk with django_bulk_load and chunking
def process_csv_bulk(df, chunk_size=50000, batch_size=10000):
    try:
        # Load existing data
        jobs, job_masks, instances, machines = load_existing_data()

        # Load existing Job-Machine mappings into memory
        existing_mappings = set(JobMachineMapping.objects.values_list('job_id', 'machine_id'))

        # Split DataFrame into chunks and process each chunk
        for df_chunk in split_dataframe(df, chunk_size):
            # Handle jobs (create or update)
            handle_jobs(df_chunk, job_masks, instances, batch_size=batch_size)
            
            # Handle machines (create only)
            handle_machines(df_chunk, jobs, instances, batch_size=batch_size)
            
            # Handle job-machine mappings
            handle_job_machine_mappings(df_chunk, jobs, machines, existing_mappings, batch_size=batch_size)

        print("CSV processing completed successfully.")
        
    except Exception as e:
        print(f"Error occurred: {e}")

# Example of reading CSV and processing in chunks
df = pd.read_csv('path_to_your_csv.csv')  # Ensure CSV has columns: job_name, machine_name, job_mask, instance, node_name, machine_type
process_csv_bulk(df)
