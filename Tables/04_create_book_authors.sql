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