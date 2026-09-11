declare begin
   dbms_scheduler.create_job(
      job_name        => 'JOB_GENERATE_OVERDUE_FINES',
      job_type        => 'STORED_PROCEDURE',
      job_action      => 'GENERATE_OVERDUE_FINES',
      start_date      => systimestamp,
      repeat_interval => 'FREQ=DAILY;BYHOUR=1;BYMINUTE=0;BYSECOND=0',
      enabled         => true
   );
end;
/