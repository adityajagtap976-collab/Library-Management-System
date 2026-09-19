from datetime import date

from pydantic import BaseModel


class ReservationCreate(BaseModel):
    book_id: int


class ReservationCreated(BaseModel):
    reservation_id: int
    reservation_date: date
    reservation_status: str
