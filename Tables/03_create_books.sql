create table books (
   book_id          number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   title            varchar2(300) not null,
   isbn             varchar2(20) not null,
   publication_date date,
   publisher_id     number(10) not null,
   genre            varchar2(80),
   constraint uq_books_isbn unique ( isbn ),
   constraint fk_books_publisher foreign key ( publisher_id )
      references publishers ( publisher_id )
);