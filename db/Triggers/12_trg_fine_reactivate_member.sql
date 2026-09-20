create or replace trigger trg_fine_reactivate_member after
   update of paid_date on fines
   for each row
declare
   v_member_id    members.member_id%type;
   v_unpaid_total number;
   v_old_status   members.member_status%type;
begin
   select member_id
     into v_member_id
     from loans
    where loan_id = :new.loan_id;

   select member_status
     into v_old_status
     from members
    where member_id = v_member_id
   for update;

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

   if
      v_unpaid_total < 2000
      and v_old_status = 'SUSPENDED'
   then
      update members
         set
         member_status = 'ACTIVE'
       where member_id = v_member_id;

      insert into member_status_history (
         member_id,
         old_status,
         new_status,
         change_reason
      ) values
         ( v_member_id,
           v_old_status,
           'ACTIVE',
           'Unpaid fines paid down below ₹2000 (remaining: ₹'
           || v_unpaid_total
           || ')' );
   end if;
end;
/