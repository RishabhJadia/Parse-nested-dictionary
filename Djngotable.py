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
