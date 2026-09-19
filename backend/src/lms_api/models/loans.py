from datetime import date

from pydantic import BaseModel


class LoanCreate(BaseModel):
    member_id: int
    copy_id: int


class LoanCreated(BaseModel):
    loan_id: int
    due_date: date


class LoanReturned(BaseModel):
    loan_id: int
    return_date: date
    copy_status: str


class LoanHistoryEntry(BaseModel):
    loan_id: int
    title: str
    isbn: str
    checkout_date: date
    due_date: date
    return_date: date | None
    is_overdue: bool


class PaginatedLoanHistory(BaseModel):
    items: list[LoanHistoryEntry]
    total: int
    limit: int
    offset: int
