   SET DEFINE OFF;

insert into reservations (
   book_id,
   member_id
) values
   ( 1,
     3 );

commit;

insert into reservations (
   book_id,
   member_id
) values
   ( 1,
     21 );

select *
  from reservations
 where book_id = 1;

insert into reservations (
   book_id,
   member_id
) values
   ( 1,
     21 );

select reservation_id,
       member_id,
       reservation_status
  from reservations
 where member_id = 21
   and reservation_status = 'WAITING';

EXEC cancel_reservation(2, 'Member no longer needs the book');

select reservation_id,
       reservation_status
  from reservations
 where reservation_id = 2;

select *
  from reservation_status_history
 where reservation_id = 2;

EXEC cancel_reservation(2, 'Trying again');