create or replace trigger trg_res_block_if_available before
   insert on reservations
   for each row
declare
   v_available_count number;
begin
   select count(*)
     into v_available_count
     from book_copies
    where book_id = :new.book_id
      and copy_status = 'AVAILABLE';

   if v_available_count > 0 then
      raise_application_error(
         -20003,
         'Cannot reserve this book: '
         || v_available_count
         || ' copy/copies currently available. Borrow directly instead.'
      );
   end if;
end;
/