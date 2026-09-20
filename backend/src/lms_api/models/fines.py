from datetime import date

from pydantic import BaseModel


class FineGenerated(BaseModel):
    fines_created: int


class FineHistoryEntry(BaseModel):
    fine_id: int
    title: str
    fine_amount: float
    fine_reason: str
    issued_date: date
    paid_date: date | None
    is_paid: bool


class PaginatedFines(BaseModel):
    items: list[FineHistoryEntry]
    total: int
    limit: int
    offset: int


class FinePaid(BaseModel):
    fine_id: int
    paid_date: date
