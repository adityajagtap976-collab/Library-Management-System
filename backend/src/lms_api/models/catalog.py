from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BookSummary(BaseModel):
    book_id: int
    title: str
    isbn: str
    publisher_name: str
    authors: list[str]
    genre: str | None


class BookCopy(BaseModel):
    copy_id: int
    copy_status: str
    shelf_location: str | None


class BookDetail(BookSummary):
    copies: list[BookCopy]


class PaginatedBooks(BaseModel):
    items: list[BookSummary]
    total: int
    limit: int
    offset: int


class BookCreate(BaseModel):
    title: str
    isbn: str = Field(min_length=10, max_length=20)
    publisher_id: int
    genre: str | None = None
    publication_date: date | None = None


class BookCopyCreate(BaseModel):
    shelf_location: str | None = None


class CopyStatusUpdate(BaseModel):
    copy_status: Literal["AVAILABLE", "ON_LOAN", "LOST", "DAMAGED", "WITHDRAWN"]
