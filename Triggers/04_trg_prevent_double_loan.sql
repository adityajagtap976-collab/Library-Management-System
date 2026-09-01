create or replace trigger trg_prevent_double_loan before
   insert on loans
   for each row
declare
   v_copy_status book_copies.copy_status%type;
begin
   select copy_status
     into v_copy_status
     from book_copies
    where copy_id = :new.copy_id;

   if v_copy_status != 'AVAILABLE' then
      raise_application_error(
         -20004,
         'Cannot create loan: copy_id '
         || :new.copy_id
         || ' is currently '
         || v_copy_status
         || ', not AVAILABLE.'
      );
   end if;
end;
/