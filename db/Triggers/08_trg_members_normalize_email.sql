create or replace trigger trg_members_normalize_email before
   insert or update of email on members
   for each row
begin
   :new.email := trim(:new.email);
end;
/