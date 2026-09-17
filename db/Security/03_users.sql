begin
   execute immediate 'create user lms_admin_user identified by "'
                     || replace(
      '&lms_admin_password',
      '"',
      '""'
   )
                     || '"';
exception
   when others then
      if sqlcode != -1920 then
         raise;
      end if;
end;
/

grant create session to lms_admin_user;
grant lms_admin_role to lms_admin_user;

begin
   execute immediate 'create user lms_member_user identified by "'
                     || replace(
      '&lms_member_password',
      '"',
      '""'
   )
                     || '"';
exception
   when others then
      if sqlcode != -1920 then
         raise;
      end if;
end;
/

grant create session to lms_member_user;
grant lms_member_role to lms_member_user;