create or replace trigger trg_author_dob_check before
   insert or update of date_of_birth on authors
   for each row
begin
   if
      :new.date_of_birth is not null
      and :new.date_of_birth > sysdate
   then
      raise_application_error(
         -20001,
         'Date of Birth cannot be in the future.'
      );
   end if;
end;
/

create or replace trigger trg_loan_set_due_date before
   insert on loans
   for each row
begin
   if :new.due_date is null then
      :new.due_date := :new.checkout_date + 14;
   end if;
end;
/

create or replace trigger trg_loan_copy_status after
   insert or update of return_date on loans
   for each row
begin
   if inserting then
      update book_copies
         set
         copy_status = 'ON_LOAN'
       where copy_id = :new.copy_id;
   elsif
      updating
      and :new.return_date is not null
      and :old.return_date is null
   then
      update book_copies
         set
         copy_status = 'AVAILABLE'
       where copy_id = :new.copy_id;
   end if;
end;
/

create or replace trigger trg_fine_suspend_member after
   insert on fines
   for each row
declare
   v_member_id    members.member_id%type;
   v_unpaid_total number;
   v_old_status   members.member_status%type;
begin
   select l.member_id
     into v_member_id
     from loans l
    where l.loan_id = :new.loan_id;

   select nvl(
      sum(f.fine_amount),
      0
   )
     into v_unpaid_total
     from fines f
     join loans l
   on l.loan_id = f.loan_id
    where l.member_id = v_member_id
      and f.paid_date is null;

   if v_unpaid_total >= 2000 then
      select member_status
        into v_old_status
        from members
       where member_id = v_member_id;
      if v_old_status = 'ACTIVE' then
         update members
            set
            member_status = 'SUSPENDED'
          where member_id = v_member_id;
         insert into member_status_history (
            member_id,
            old_status,
            new_status,
            change_reason
         ) values
            ( v_member_id,
              v_old_status,
              'SUSPENDED',
              'Unpaid fines exceeded ₹2000 (total: ₹'
              || v_unpaid_total
              || ')' );
      end if;
   end if;
end;
/