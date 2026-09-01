create or replace trigger trg_loan_copy_status after
   insert or update of return_date on loans
   for each row
declare
   v_book_id            book_copies.book_id%type;
   v_reservation_id     reservations.reservation_id%type;
   v_reservation_member reservations.member_id%type;
begin
   if inserting then
      update book_copies
         set
         copy_status = 'ON_LOAN'
       where copy_id = :new.copy_id;

   elsif
      updating
      and :new.return_date is not null
      and :old.return_date is null
   then
      select book_id
        into v_book_id
        from book_copies
       where copy_id = :new.copy_id;

      begin
         select reservation_id,
                member_id
           into
            v_reservation_id,
            v_reservation_member
           from (
            select reservation_id,
                   member_id
              from reservations
             where book_id = v_book_id
               and reservation_status = 'WAITING'
             order by reservation_date asc
         )
          where rownum = 1;

         update reservations
            set reservation_status = 'FULFILLED',
                fulfilled_date = sysdate
          where reservation_id = v_reservation_id;

         update book_copies
            set
            copy_status = 'ON_LOAN'
          where copy_id = :new.copy_id;

      exception
         when no_data_found then
            update book_copies
               set
               copy_status = 'AVAILABLE'
             where copy_id = :new.copy_id;
      end;

   end if;
end;
/