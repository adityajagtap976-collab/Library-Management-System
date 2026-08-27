create table publishers (
   publisher_id   number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   publisher_name varchar2(150) not null,
   country        varchar2(80),
   contact_email  varchar2(150) unique,
   constraint uq_publisher_name unique ( publisher_name )
);

create table authors (
   author_id     number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   first_name    varchar2(80) not null,
   last_name     varchar2(80) not null,
   date_of_birth date,
   nationality   varchar2(80)
);

create table books (
   book_id      number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   title        varchar2(300) not null,
   isbn         varchar2(20) not null,
   publisher_id number(10) not null,
   genre        varchar2(80),
   constraint uq_books_isbn unique ( isbn ),
   constraint fk_books_publisher foreign key ( publisher_id )
      references publishers ( publisher_id )
);

create table book_authors (
   book_id   number(10) not null,
   author_id number(10) not null,
   constraint pk_book_authors primary key ( book_id,
                                            author_id ),
   constraint fk_ba_book foreign key ( book_id )
      references books ( book_id )
         on delete cascade,
   constraint fk_ba_author foreign key ( author_id )
      references authors ( author_id )
         on delete cascade
);

create table book_copies (
   copy_id        number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   book_id        number(10) not null,
   copy_status    varchar2(20) default 'AVAILABLE' not null,
   shelf_location varchar2(50),
   aquired_date   date default sysdate not null,
   constraint fk_copies_book foreign key ( book_id )
      references book ( book_id ),
   constraint chk_copy_status
      check ( copy_status in ( 'AVAILABLE',
                               'ON_LOAN',
                               'LOST',
                               'DAMAGED',
                               'WITHDRAWN' ) )
);

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

create table loans (
   loan_id       number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   copy_id       number(10) not null,
   member_id     number(10) not null,
   checkout_date date default sysdate not null,
   due_date      date not null,
   return_date   date,
   constraint fk_loan_copy foreign key ( copy_id )
      references book_copies ( copy_id ),
   constraint fk_loan_members foreign key ( member_id )
      references members ( member_id ),
   constraint chk_loan_dates
      check ( return_date is null
          or return_date >= checkout_date )
);