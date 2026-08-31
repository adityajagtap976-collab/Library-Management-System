-- ============================================================
-- MASTER BUILD SCRIPT — Library Management System
-- Run from the project root. Assumes Tables/ and Triggers/ subfolders.
-- ============================================================

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
   for t in (
      select table_name
        from user_tables
       where table_name in ( 'MEMBER_STATUS_HISTORY',
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

pro    -- publishers
@@Tables/01_create_publishers.sql
pro    -- authors
@@Tables/02_create_authors.sql
pro    -- books
@@Tables/03_create_books.sql
pro    -- book_authors
@@Tables/04_create_book_authors.sql
pro    -- book_copies
@@Tables/05_create_book_copies.sql
pro    -- members
@@Tables/06_create_members.sql
pro    -- loans
@@Tables/07_create_loans.sql
pro    -- fines
@@Tables/08_create_fines.sql
pro    -- reservations
@@Tables/09_create_reservations.sql
pro    -- member_status_history
@@Tables/10_create_member_status_history.sql

pro    ============================================
pro    STEP 3: CREATING TRIGGERS
pro    ============================================

@@Triggers/01_trg_author_dob_check.sql
SHOW ERRORS TRIGGER trg_author_dob_check;

@@Triggers/02_trg_prevent_sole_author_delete.sql
SHOW ERRORS TRIGGER trg_prevent_sole_author_delete;

@@Triggers/03_trg_loan_set_due_date.sql
SHOW ERRORS TRIGGER trg_loan_set_due_date;

@@Triggers/04_trg_loan_copy_status.sql
SHOW ERRORS TRIGGER trg_loan_copy_status;

@@Triggers/05_trg_fine_suspend_member.sql
SHOW ERRORS TRIGGER trg_fine_suspend_member;

@@Triggers/06_trg_res_block_if_available.sql
SHOW ERRORS TRIGGER trg_res_block_if_available;

pro    ============================================
pro    STEP 4: VERIFICATION
pro    ============================================

pro    -- Table count check (expect 10)
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
                       'MEMBER_STATUS_HISTORY' );

pro    -- Trigger status check (all must be ENABLED, none INVALID)
select trigger_name,
       status
  from user_triggers
 order by trigger_name;

pro    -- Object validity check (all must show VALID)
select object_name,
       object_type,
       status
  from user_objects
 where status != 'VALID';

pro    ============================================
pro    BUILD COMPLETE — review build_log.txt for full detail
pro    ============================================

SPOOL OFF