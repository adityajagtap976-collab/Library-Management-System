create or replace trigger trg_prevent_sole_author_delete before
   delete on authors
   for each row
declare
   v_orphan_count number;
begin
   select count(*)
     into v_orphan_count
     from book_authors ba
    where ba.author_id = :old.author_id
      and not exists (
      select 1
        from book_authors ba2
       where ba2.book_id = ba.book_id
         and ba2.author_id != :old.author_id
   );

   if v_orphan_count > 0 then
      raise_application_error(
         -20002,
         'Cannot delete author '
         || :old.author_id
         || ': they are the sole author of '
         || v_orphan_count
         || ' book(s). Reassign or delete those books first.'
      );
   end if;
end;
/