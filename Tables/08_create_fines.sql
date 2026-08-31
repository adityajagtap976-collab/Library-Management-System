create table fines (
   fine_id     number(10) generated always as identity ( start with 1 increment by 1 ) primary key,
   loan_id     number(10) not null,
   fine_amount number(6,2) not null,
   fine_reason varchar2(20 char) not null,
   issued_date date default sysdate not null,
   paid_date   date,
   constraint fk_fines_loan foreign key ( loan_id )
      references loans ( loan_id ),
   constraint chk_fine_amount check ( fine_amount > 0 ),
   constraint chk_fine_reason
      check ( fine_reason in ( 'LATE_RETURN',
                               'LOST',
                               'DAMAGED' ) ),
   constraint chk_fine_paid_date
      check ( paid_date is null
          or paid_date >= issued_date )
);