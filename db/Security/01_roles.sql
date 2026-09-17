begin
   execute immediate 'create role lms_admin_role';
exception
   when others then
      if sqlcode != -1921 then
         raise;
      end if;
end;
/

begin
   execute immediate 'create role lms_member_role';
exception
   when others then
      if sqlcode != -1921 then
         raise;
      end if;
end;
/