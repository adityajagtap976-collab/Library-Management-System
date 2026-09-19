import oracledb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from lms_api.core.dependencies import Principal, get_current_principal
from lms_api.db.session import get_connection
from lms_api.models.catalog import BookDetail, BookSummary, PaginatedBooks
from lms_api.repositories.catalog import count_books, get_book_by_id, list_books

router = APIRouter(prefix="/books")


@router.get("", response_model=PaginatedBooks)
async def get_books(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(get_current_principal),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> PaginatedBooks:
    items = [
        BookSummary(**book) for book in await list_books(connection, limit, offset)
    ]
    total = await count_books(connection)
    return PaginatedBooks(items=items, total=total, limit=limit, offset=offset)


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(
    book_id: int,
    _principal: Principal = Depends(get_current_principal),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> BookDetail:
    book = await get_book_by_id(connection, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return BookDetail(**book)
