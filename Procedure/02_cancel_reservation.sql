create or replace procedure cancel_reservation (
   p_reservation_id in reservations.reservation_id%type,
   p_reason         in varchar2
) as
   v_current_status reservations.reservation_status%type;
begin
   select reservation_status
     into v_current_status
     from reservations
    where reservation_id = p_reservation_id
   for update;

   if v_current_status != 'WAITING' then
      raise_application_error(
         -20005,
         'Cannot cancel reservation'
         || v_current_status
         || ', not WAITING.'
      );
   end if;

   update reservations
      set
      reservation_status = 'CANCELLED'
    where reservation_id = p_reservation_id;

   insert into reservation_status_history (
      reservation_id,
      old_status,
      new_status,
      change_reason
   ) values
      ( p_reservation_id,
        'WAITING',
        'CANCELLED',
        p_reason );
end;
/