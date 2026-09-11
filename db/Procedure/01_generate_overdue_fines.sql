create or replace procedure generate_overdue_fines as
begin
   for ln in (
      select l.loan_id,
             l.due_date
        from loans l
       where l.return_date is null
         and l.due_date < trunc(sysdate)
         and not exists (
         select 1
           from fines f
          where f.loan_id = l.loan_id
            and f.fine_reason = 'LATE_RETURN'
      )
   ) loop
      insert into fines (
         loan_id,
         fine_amount,
         fine_reason
      ) values
         ( ln.loan_id,
           ( trunc(sysdate) - ln.due_date ) * 10,
           'LATE_RETURN' );
   end loop;
end;
/

alter procedure generate_overdue_fines compile;

select object_name,
       object_type,
       status
  from user_objects
 where status != 'VALID';
-- expect: 0 rows