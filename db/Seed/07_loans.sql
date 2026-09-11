   SET DEFINE OFF;

-- Case 1: Alice legitimately borrows copy A
insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 1,
     1,
     null );
commit;

-- Case 2: THE ACTUAL TEST — try to loan the SAME copy to Bob while Alice still has it
insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 1,
     2,
     null );
-- expect: ORA-20004, this must fail

-- Case 3: Bob borrows the OTHER copy instead — must succeed, proving legitimate loans still work
insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 2,
     2,
     null );
commit;

select loan_id,
       copy_id,
       member_id,
       return_date
  from loans
 where copy_id in ( 1,
                    2 );

update loans
   set
   due_date = trunc(sysdate) - 5
 where loan_id = 1;

update loans
   set
   return_date = sysdate
 where loan_id = 1
   and return_date is null;