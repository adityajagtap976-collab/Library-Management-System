create or replace trigger trg_loan_set_due_date before
   insert on loans
   for each row
begin
   if :new.due_date is null then
      :new.due_date := :new.checkout_date + 14;
   end if;
end;
/