create or replace trigger trg_fine_suspend_member for
   insert on fines
compound trigger
   type t_loan_ids is
      table of fines.loan_id%type index by pls_integer;
   v_loan_ids t_loan_ids;
   v_count    pls_integer := 0;
   after each row is begin
      v_count := v_count + 1;
      v_loan_ids(v_count) := :new.loan_id;
   end after each row;
   after statement is
      v_member_id    members.member_id%type;
      v_unpaid_total number;
      v_old_status   members.member_status%type;
   begin
      for i in 1..v_count loop
         select l.member_id
           into v_member_id
           from loans l
          where l.loan_id = v_loan_ids(i);

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

      end loop;
   end after statement;
end trg_fine_suspend_member;
/

SHOW ERRORS TRIGGER trg_fine_suspend_member;