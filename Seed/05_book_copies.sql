   SET DEFINE OFF;

insert into book_copies (
   book_id,
   shelf_location
) values
   ( 1,
     'A3' );
insert into book_copies (
   book_id,
   shelf_location
) values
   ( 1,
     'A4' );

select copy_id,
       copy_status
  from book_copies
 where book_id = 1;