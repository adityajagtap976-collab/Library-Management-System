   SET DEFINE OFF;

insert into members (
   first_name,
   last_name,
   email
) values
   ( 'Alice',
     'Borrower',
     'alice@test.com' );
insert into members (
   first_name,
   last_name,
   email
) values
   ( 'Bob',
     'Waiter',
     'bob@test.com' );

insert into members (
   first_name,
   last_name,
   email
) values
   ( 'Carol',
     'Reserver',
     'carol@test.com' );

select member_id,
       first_name,
       last_name,
       email
  from members;