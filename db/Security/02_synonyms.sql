declare
   v_owner varchar2(128) := upper('&lms_owner');
begin
   for object_name in (
      select column_value as name
        from table ( sys.odcivarchar2list(
         'PUBLISHERS',
         'AUTHORS',
         'BOOKS',
         'BOOK_AUTHORS',
         'BOOK_COPIES',
         'MEMBERS',
         'LOANS',
         'FINES',
         'RESERVATIONS',
         'MEMBER_STATUS_HISTORY',
         'RESERVATION_STATUS_HISTORY',
         'GENERATE_OVERDUE_FINES',
         'CANCEL_RESERVATION'
      ) )
   ) loop
      begin
         execute immediate 'drop public synonym ' || lower(object_name.name);
      exception
         when others then
            if sqlcode != -1432 then
               raise;
            end if;
      end;

      execute immediate 'create public synonym '
                        || lower(object_name.name)
                        || ' for '
                        || v_owner
                        || '.'
                        || lower(object_name.name);
   end loop;
end;
/