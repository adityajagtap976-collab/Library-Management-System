   SET DEFINE OFF;
SET ECHO ON;
SET FEEDBACK ON;

WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK;

pro    ============================================
pro    DEPLOYING SCHEDULER JOBS
pro    ============================================

begin
   for j in (
      select job_name
        from user_scheduler_jobs
       where job_name = 'JOB_GENERATE_OVERDUE_FINES'
   ) loop
      dbms_scheduler.drop_job(
         job_name => j.job_name,
         force    => true
      );
   end loop;
end;
/

@@../db/Jobs/01_job_overdue_fines_schedule.sql

pro    SCHEDULER DEPLOYMENT COMPLETE