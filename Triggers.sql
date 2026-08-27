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

create or replace trigger trg_loan_set_due_date before
   insert on loans
   for each row
begin
   if :new.due_date is null then
      :new.due_date := :new.checkout_date + 14;
   end if;
end;
/

create or replace trigger trg_loan_copy_status after
   insert or update of return_date on loans
   for each row
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
      update book_copies
         set
         copy_status = 'AVAILABLE'
       where copy_id = :new.copy_id;
   end if;
end;
/