   SET DEFINE OFF;
SET ECHO ON;
SET FEEDBACK ON;

pro    ============================================
pro    RUNNING BEHAVIOR CHECKS
pro    ============================================

pro    -- The first loan should set the copy to ON_LOAN.
select copy_id,
       copy_status
  from book_copies
 where copy_id = 1;

pro    -- The second loan should set the other copy to ON_LOAN.
select loan_id,
       copy_id,
       member_id,
       return_date
  from loans
 where copy_id in ( 1,
                    2 )
 order by loan_id;

pro    -- Overdue-fine generation should be idempotent for loan 1.
exec generate_overdue_fines;

select loan_id,
       fine_reason,
       count(*) as fine_count
  from fines
 where loan_id = 1
 group by loan_id,
          fine_reason;

pro    -- Reservation status history should exist for cancelled reservations.
select reservation_id,
       old_status,
       new_status,
       change_reason
  from reservation_status_history
 order by history_id;