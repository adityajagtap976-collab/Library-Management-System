   SET DEFINE OFF;
SET ECHO ON;
SET FEEDBACK ON;

SPOOL seed_demo_log.txt

pro    ============================================
pro    LOADING DEMO DATA
pro    ============================================

@@../db/seeds/01_publisher.sql
@@../db/seeds/02_authors.sql
@@../db/seeds/03_books.sql
@@../db/seeds/04_book_authors.sql
@@../db/seeds/05_book_copies.sql
@@../db/seeds/06_members.sql
@@../db/seeds/07_loans.sql
@@../db/seeds/08_fines.sql
@@../db/seeds/09_reservation.sql
@@../db/seeds/10_member_status_history.sql

commit;

pro    DEMO DATA LOAD COMPLETE

SPOOL OFF