create or replace trigger trg_staff_normalize_email before
   insert or update of email on staff
   for each row
begin
   :new.email := trim(:new.email);
end;
/