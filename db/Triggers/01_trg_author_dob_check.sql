create or replace trigger trg_author_dob_check before
   insert or update of date_of_birth on authors
   for each row
begin
   if
      :new.date_of_birth is not null
      and :new.date_of_birth > sysdate
   then
      raise_application_error(
         -20001,
         'Date of Birth cannot be in the future.'
      );
   end if;
end;
/