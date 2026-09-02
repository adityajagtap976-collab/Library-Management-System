   SET DEFINE OFF;

exec generate_overdue_fines;

select *
  from fines
 where loan_id = 1;

select count(*)
  from fines
 where loan_id = 1
   and fine_reason = 'LATE_RETURN';