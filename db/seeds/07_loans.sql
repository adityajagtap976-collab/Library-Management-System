   SET DEFINE OFF;

insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 1,
     1,
     trunc(sysdate) - 5 );

insert into loans (
   copy_id,
   member_id,
   due_date
) values
   ( 2,
     2,
     trunc(sysdate) + 14 );
commit;