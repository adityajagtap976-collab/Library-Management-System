   SET DEFINE OFF;

insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 1,
     1,
     null );

update loans
   set
   return_date = sysdate
 where copy_id = 1
   and return_date is null;

commit;

select *
  from loans;