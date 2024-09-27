WITH job_data AS (
  SELECT 
    j.id, 
    j.name AS job_name, 
    j.job_type, 
    j.box_name, 
    j.owner, 
    j.alarm_if_fail, 
    j.alarm_if_terminate, 
    j.is_active, 
    j.create_date, 
    j.update_date,
    a.name AS autosys_instance_name, 
    jm.name AS job_mask_name
  FROM job_table j
  LEFT JOIN autosys_instance_table a ON j.autosys_instance_id = a.id
  LEFT JOIN job_mask_table jm ON j.job_mask_id = jm.id
  ORDER BY j.name
  LIMIT 1000 -- Adjust for pagination size
),
machine_data AS (
  SELECT 
    m.id AS machine_id, 
    m.name AS machine_name, 
    jm.job_id
  FROM machine_table m
  JOIN job_machines_table jm ON m.id = jm.machine_id
)
SELECT 
  jd.*, 
  array_agg(json_build_object('id', md.machine_id, 'name', md.machine_name)) AS machines
FROM job_data jd
LEFT JOIN machine_data md ON jd.id = md.job_id
GROUP BY jd.id;
