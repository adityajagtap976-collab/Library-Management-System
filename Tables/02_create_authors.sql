create table authors (
   author_id     number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   first_name    varchar2(80) not null,
   last_name     varchar2(80) not null,
   date_of_birth date,
   nationality   varchar2(80)
);