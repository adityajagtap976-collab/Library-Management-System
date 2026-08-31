create table members (
   member_id       number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   first_name      varchar2(80) not null,
   last_name       varchar2(80) not null,
   email           varchar2(150) not null,
   phone           varchar2(20),
   membership_date date default sysdate not null,
   member_status   varchar2(20) default 'ACTIVE' not null,
   constraint uq_members_email unique ( email ),
   constraint chk_member_status
      check ( member_status in ( 'ACTIVE',
                                 'SUSPENDED',
                                 'EXPIRED' ) )
);