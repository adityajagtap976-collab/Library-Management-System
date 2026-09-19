create or replace trigger trg_publishers_normalize_identity before
   insert or update of publisher_name,contact_email on publishers
   for each row
begin
   :new.publisher_name := trim(:new.publisher_name);
   :new.contact_email := trim(:new.contact_email);
end;
/