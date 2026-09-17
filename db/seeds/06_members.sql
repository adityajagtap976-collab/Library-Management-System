   SET DEFINE OFF;

insert into members (
   first_name,
   last_name,
   email,
   password_hash
) values
   ( 'Alice',
     'Borrower',
     'alice@test.com',
     'demo_hash_alice' );
insert into members (
   first_name,
   last_name,
   email,
   password_hash
) values
   ( 'Bob',
     'Waiter',
     'bob@test.com',
     'demo_hash_bob' );

insert into members (
   first_name,
   last_name,
   email,
   password_hash
) values
   ( 'Carol',
     'Reserver',
     'carol@test.com',
     'demo_hash_carol' );

select member_id,
       first_name,
       last_name,
       email
  from members;