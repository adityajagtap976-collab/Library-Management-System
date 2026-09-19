from datetime import date

from pydantic import BaseModel


class LoanCreate(BaseModel):
    member_id: int
    copy_id: int


class LoanCreated(BaseModel):
    loan_id: int
    due_date: date
