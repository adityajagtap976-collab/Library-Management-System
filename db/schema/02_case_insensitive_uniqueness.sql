alter table members drop constraint uq_members_email;
alter table staff drop constraint uq_staff_email;
alter table publishers drop constraint uq_publisher_email;
alter table publishers drop constraint uq_publisher_name;

update members
   set
   email = trim(email)
 where email <> trim(email);

update staff
   set
   email = trim(email)
 where email <> trim(email);

update publishers
   set publisher_name = trim(publisher_name),
       contact_email = trim(contact_email)
 where publisher_name <> trim(publisher_name)
    or contact_email <> trim(contact_email);

select lower(email),
       count(*)
  from members
 group by lower(email)
having count(*) > 1;

select lower(email),
       count(*)
  from staff
 group by lower(email)
having count(*) > 1;

select lower(publisher_name),
       count(*)
  from publishers
 group by lower(publisher_name)
having count(*) > 1;

create unique index uq_members_email_ci on
   members ( lower(email) );
create unique index uq_staff_email_ci on
   staff ( lower(email) );
create unique index uq_publisher_email_ci on
   publishers ( lower(contact_email) );
create unique index uq_publisher_name_ci on
   publishers ( lower(publisher_name) );