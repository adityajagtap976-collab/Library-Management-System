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

select *
  from members;