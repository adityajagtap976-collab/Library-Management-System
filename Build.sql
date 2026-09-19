   SET DEFINE OFF;
SET ECHO ON;
SET FEEDBACK ON;

   SPOOL build_log.txt

WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK;

pro    ============================================
pro    STEP 1: DROPPING EXISTING TABLES (if any)
pro    ============================================

WHENEVER SQLERROR CONTINUE;

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

begin
   for t in (
      select table_name
        from user_tables
       where table_name in ( 'MEMBER_STATUS_HISTORY',
                             'RESERVATION_STATUS_HISTORY',
                             'STAFF',
                             'RESERVATIONS',
                             'FINES',
                             'LOANS',
                             'MEMBERS',
                             'BOOK_COPIES',
                             'BOOK_AUTHORS',
                             'BOOKS',
                             'AUTHORS',
                             'PUBLISHERS' )
   ) loop
      execute immediate 'DROP TABLE '
                        || t.table_name
                        || ' CASCADE CONSTRAINTS';
      dbms_output.put_line('Dropped: ' || t.table_name);
   end loop;
end;
/

WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK;

pro    ============================================
pro    STEP 2: CREATING TABLES (dependency order)
pro    ============================================

@@db/schema/01_schema.sql
@@db/schema/02_case_insensitive_uniqueness.sql

commit;

pro    ============================================
pro    STEP 3: CREATING TRIGGERS
pro    ============================================

@@db/Triggers/01_trg_author_dob_check.sql
SHOW ERRORS TRIGGER trg_author_dob_check;

@@db/Triggers/02_trg_prevent_sole_author_delete.sql
SHOW ERRORS TRIGGER trg_prevent_sole_author_delete;

@@db/Triggers/03_trg_loan_copy_status.sql
SHOW ERRORS TRIGGER trg_loan_copy_status;

@@db/Triggers/04_trg_prevent_double_loan.sql
SHOW ERRORS TRIGGER trg_prevent_double_loan;

@@db/Triggers/05_trg_loan_set_due_date.sql
SHOW ERRORS TRIGGER trg_loan_set_due_date;

@@db/Triggers/06_trg_fine_suspend_member.sql
SHOW ERRORS TRIGGER trg_fine_suspend_member;

@@db/Triggers/07_trg_res_block_if_available.sql
SHOW ERRORS TRIGGER trg_res_block_if_available;

@@db/Triggers/08_trg_members_normalize_email.sql
SHOW ERRORS TRIGGER trg_members_normalize_email;

@@db/Triggers/09_trg_staff_normalize_email.sql
SHOW ERRORS TRIGGER trg_staff_normalize_email;

@@db/Triggers/10_trg_publishers_normalize_identity.sql
SHOW ERRORS TRIGGER trg_publishers_normalize_identity;

commit;

pro    ============================================
pro    STEP 4: CREATING PROCEDURES
pro    ============================================

@@db/procedures/01_generate_overdue_fines.sql
SHOW ERRORS PROCEDURE generate_overdue_fines;

@@db/procedures/02_cancel_reservation.sql
SHOW ERRORS PROCEDURE cancel_reservation;

commit;

pro    ============================================
pro    STEP 5: VERIFICATION
pro    ============================================

pro    -- Table count check (expect 12)
select count(*) as table_count
  from user_tables
 where table_name in ( 'PUBLISHERS',
                       'AUTHORS',
                       'BOOKS',
                       'BOOK_AUTHORS',
                       'BOOK_COPIES',
                       'MEMBERS',
                       'LOANS',
                       'FINES',
                       'RESERVATIONS',
                       'MEMBER_STATUS_HISTORY',
                       'RESERVATION_STATUS_HISTORY',
                       'STAFF' );

pro    -- Trigger count + status check (expect 10 rows, all ENABLED)
select trigger_name,
       status
  from user_triggers
 order by trigger_name;

pro    -- Object validity check (expect 0 rows)
select object_name,
       object_type,
       status
  from user_objects
 where status != 'VALID';

pro    ============================================
pro    BUILD COMPLETE — review build_log.txt for full detail
pro    ============================================

SPOOL OFF