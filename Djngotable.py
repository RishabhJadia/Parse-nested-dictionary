from django.db import connection
import pandas as pd

def fetch_jobs_in_batches(limit, offset):
    # Raw SQL query
    raw_sql = """
        SELECT
            job.id,
            job.name,
            job.job_type,
            job.box_name,
            job.owner,
            job.alarm_if_fail,
            job.alarm_if_terminate,
            job.is_active,
            instance.name AS autosys_instance,
            mask.name AS job_mask,
            machine.id AS machine_id,
            machine.name AS machine_name,
            job.create_date,
            job.update_date
        FROM job
        LEFT JOIN autosys_instance instance ON job.autosys_instance_id = instance.id
        LEFT JOIN job_mask mask ON job.job_mask_id = mask.id
        LEFT JOIN job_machines jm ON job.id = jm.job_id
        LEFT JOIN machine ON jm.machine_id = machine.id
        ORDER BY job.id
        LIMIT %s OFFSET %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(raw_sql, [limit, offset])
        columns = [col[0] for col in cursor.description]
        results = cursor.fetchall()

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(results, columns=columns)
    return df

# Example: Fetch data in batches of 10,000 records
batch_size = 10000
offset = 0
all_data = pd.DataFrame()  # Empty DataFrame to store results

while True:
    batch_data = fetch_jobs_in_batches(batch_size, offset)
    if batch_data.empty:
        break  # No more records to fetch

    # Append batch data to all_data DataFrame
    all_data = pd.concat([all_data, batch_data], ignore_index=True)

    # Update offset for the next batch
    offset += batch_size

# Now you have all the data in all_data DataFrame
print(all_data)
