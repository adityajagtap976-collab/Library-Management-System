from pydantic import BaseModel


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
