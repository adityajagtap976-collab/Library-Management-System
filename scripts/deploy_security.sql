   SET DEFINE ON;
SET ECHO ON;
SET FEEDBACK ON;

WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK;

pro    ============================================
pro    DEPLOYING SECURITY (DBA PRIVILEGES REQUIRED)
pro    ============================================

accept lms_owner char prompt 'Application owner schema [PRACTICE]: ' default 'PRACTICE'
accept lms_admin_password char prompt 'Admin user password: ' hide
accept lms_member_password char prompt 'Member user password: ' hide

@@../db/Security/01_roles.sql
@@../db/Security/03_users.sql
@@../db/Security/02_synonyms.sql
@@../db/Grants/01_grant_admin_role.sql
@@../db/Grants/02_grant_member_role.sql

pro    SECURITY DEPLOYMENT COMPLETE