create table loans (
   loan_id       number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   copy_id       number(10) not null,
   member_id     number(10) not null,
   checkout_date date default sysdate not null,
   due_date      date not null,
   return_date   date,
   constraint fk_loans_copy foreign key ( copy_id )
      references book_copies ( copy_id ),
   constraint fk_loans_member foreign key ( member_id )
      references members ( member_id ),
   constraint chk_loans_date
      check ( return_date is null
          or return_date >= checkout_date )
);