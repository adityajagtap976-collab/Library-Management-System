create table reservations (
   reservation_id     number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   book_id            number(10) not null,
   member_id          number(10) not null,
   reservation_date   date default sysdate not null,
   reservation_status varchar2(20 char) default 'WAITING' not null,
   fulfilled_date     date,
   constraint fk_res_book foreign key ( book_id )
      references books ( book_id ),
   constraint fk_res_member foreign key ( member_id )
      references members ( member_id ),
   constraint chk_res_status
      check ( reservation_status in ( 'WAITING',
                                      'FULFILLED',
                                      'CANCELLED' ) ),
   constraint uq_res_active_member_book unique ( book_id,
                                                 member_id,
                                                 reservation_status )
);