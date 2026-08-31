create table member_status_history (
   history_id    number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   member_id     number(10) not null,
   old_status    varchar2(20 char),
   new_status    varchar2(20 char) not null,
   change_reason varchar2(200 char) not null,
   changed_date  date default sysdate not null,
   constraint fk_history_member foreign key ( member_id )
      references members ( member_id )
);