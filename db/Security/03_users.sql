create user lms_admin_user identified by "Aditya@123";
grant create session to lms_admin_user;
grant lms_admin_role to lms_admin_user;

create user lms_member_user identified by "Jagtap@123";
grant create session to lms_member_user;
grant lms_member_role to lms_member_user;