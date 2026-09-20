alter table reservations drop constraint uq_res_active_member_book;

create unique index uq_res_active_member_book on
   reservations (
      case
         when
            reservation_status
         = 'WAITING' then
               book_id
      end,
      case
         when
            reservation_status
         = 'WAITING' then
               member_id
      end
   );