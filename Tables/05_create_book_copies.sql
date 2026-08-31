create table book_copies (
   copy_id        number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   book_id        number(10) not null,
   copy_status    varchar2(20) default 'AVAILABLE' not null,
   shelf_location varchar2(50),
   acquired_date  date default sysdate not null,
   constraint fk_copies_book foreign key ( book_id )
      references books ( book_id ),
   constraint chk_copy_status
      check ( copy_status in ( 'AVAILABLE',
                               'ON_LOAN',
                               'LOST',
                               'DAMAGED',
                               'WITHDRAWN' ) )
);