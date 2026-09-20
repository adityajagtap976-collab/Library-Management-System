from datetime import date

from pydantic import BaseModel


class ReservationCreate(BaseModel):
    book_id: int


class ReservationCreated(BaseModel):
    reservation_id: int
    reservation_date: date
    reservation_status: str


class ReservationHistoryEntry(BaseModel):
    reservation_id: int
    title: str
    isbn: str
    reservation_date: date
    reservation_status: str
    fulfilled_date: date | None


class PaginatedReservations(BaseModel):
    items: list[ReservationHistoryEntry]
    total: int
    limit: int
    offset: int
