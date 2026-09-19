create or replace trigger trg_prevent_suspended_loan before
   insert on loans
   for each row
declare
   v_status members.member_status%type;
begin
   select member_status
     into v_status
     from members
    where member_id = :new.member_id;

   if v_status != 'ACTIVE' then
      raise_application_error(
         -20005,
         'Member '
         || :new.member_id
         || ' is '
         || v_status
         || ' and cannot check out books.'
      );
   end if;
end;
/