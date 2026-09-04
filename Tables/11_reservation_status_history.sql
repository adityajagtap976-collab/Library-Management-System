create table reservation_status_history (
   history_id     number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   reservation_id number(10) not null,
   old_status     varchar2(20),
   new_status     varchar2(20) not null,
   change_reason  varchar2(200) not null,
   change_date    date default sysdate not null,
   constraint fk_res_history_reservation foreign key ( reservation_id )
      references reservations ( reservation_id )
);