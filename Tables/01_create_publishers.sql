create table publishers (
   publisher_id   number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   publisher_name varchar2(150) not null,
   country        varchar2(80),
   contact_email  varchar2(150),
   constraint uq_publisher_name unique ( publisher_name ),
   constraint uq_publisher_email unique ( contact_email )
);