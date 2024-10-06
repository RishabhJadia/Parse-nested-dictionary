SELECT 
    job.id AS job_id,
    job.name AS job_name,
    job.job_type,
    job.box_name,
    job.owner,
    job.alarm_if_fail,
    job.alarm_if_terminate,
    job.is_active,
    instance.name AS instance_name,
    mask.name AS job_mask_name,
    machine.id AS machine_id,
    machine.name AS machine_name,
    job.create_date,
    job.update_date
FROM autosys_db_job AS job
LEFT JOIN autosys_db_autosysinstance AS instance ON job.autosys_instance_id = instance.id
LEFT JOIN autosys_db_jobmask AS mask ON job.job_mask_id = mask.id
LEFT JOIN autosys_db_jobmachinemapling AS mapping ON job.id = mapping.job_id
LEFT JOIN autosys_db_machine AS machine ON mapping.machine_id = machine.id
WHERE job.is_active = TRUE;

-------------------


from django.db import connection
import pandas as pd

def fetch_job_machine_data(page_size=1000):
    """
    Fetch job and machine data from the database using pagination.
    
    Args:
        page_size (int): The number of records to fetch per page.

    Returns:
        pd.DataFrame: A DataFrame containing the merged job and machine data.
    """
    page_number = 0
    all_results = []  # List to collect DataFrames

    while True:
        offset = page_number * page_size

        # Load job data with joins
        job_query = f"""
        SELECT 
            j.id AS job_id,
            j.name AS job_name,
            j.job_type,
            j.box_name,
            j.owner,
            j.alarm_if_fail,
            j.alarm_if_terminate,
            j.is_active,
            j.create_date,
            j.update_date,
            ai.name AS autosys_instance_name,
            jm.mask AS job_mask_name
        FROM 
            autosys_db_job j
        LEFT JOIN 
            autosys_db_autosysinstance ai ON j.autosys_instance_id = ai.id
        LEFT JOIN 
            autosys_db_jobmask jm ON j.job_mask_id = jm.id
        LIMIT {page_size} OFFSET {offset};  -- Pagination
        """

        # Fetch job data into a DataFrame
        job_df = pd.read_sql_query(job_query, connection)

        # If no job data is returned, break the loop
        if job_df.empty:
            break

        # Load machine mapping data with pagination
        machine_query = f"""
        SELECT 
            jm.job_id,
            md.id AS machine_id,
            md.name AS machine_name
        FROM 
            autosys_db_jobmachinemapling jm
        LEFT JOIN 
            autosys_db_machine md ON jm.machine_id = md.id
        LIMIT {page_size} OFFSET {offset};  -- Pagination
        """

        # Fetch machine data into a DataFrame
        machine_df = pd.read_sql_query(machine_query, connection)

        # Merge job data with machine data
        result_df = pd.merge(job_df, machine_df, on='job_id', how='left')

        # Append the result DataFrame to the list
        all_results.append(result_df)

        # Move to the next page
        page_number += 1

    # Concatenate all the DataFrames in the list into a single DataFrame
    final_df = pd.concat(all_results, ignore_index=True)

    return final_df

# Example usage
if __name__ == "__main__":
    # This example assumes you are running this code within a Django context.
    df = fetch_job_machine_data()
    print(df.head())  # Print the first few rows of the final DataFrame
