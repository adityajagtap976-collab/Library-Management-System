CREATE TABLE publishers (
  publisher_id NUMBER(10) GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
  publisher_name VARCHAR2(150) NOT NULL,
  country VARCHAR2(80),
  contact_email VARCHAR2(150) UNIQUE,
  CONSTRAINT uq_publisher_name UNIQUE (publisher_name)
);

CREATE TABLE authors (
  author_id NUMBER(10) GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
  first_name VARCHAR2(80) NOT NULL,
  last_name VARCHAR2(80) NOT NULL,
  date_of_birth DATE,
  nationality VARCHAR2(80)
);

CREATE OR REPLACE TRIGGER trg_author_dob_check
BEFORE INSERT OR UPDATE OF date_of_birth ON authors
FOR EACH ROW
BEGIN
  IF :NEW.date_of_birth IS NOT NULL AND :NEW.date_of_birth > SYSDATE THEN RAISE_APPLICATION_ERROR(-20001, 'Date of Birth cannot be in the future.');
  END IF;
END;
/