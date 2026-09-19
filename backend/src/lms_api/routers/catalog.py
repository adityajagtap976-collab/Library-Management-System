import oracledb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from lms_api.core.dependencies import Principal, get_current_principal, require_role
from lms_api.db.session import get_connection
from lms_api.models.catalog import (
    BookCopyCreate,
    BookCreate,
    BookDetail,
    BookSummary,
    CopyStatusUpdate,
    PaginatedBooks,
)
from lms_api.repositories.catalog import (
    add_book_copy,
    count_books,
    create_book,
    get_book_by_id,
    list_books,
    update_copy_status,
)

router = APIRouter(prefix="/books")


def _database_error_code(error: oracledb.DatabaseError) -> int | None:
    database_error = error.args[0] if error.args else None
    code = getattr(database_error, "code", None)
    return int(code) if code is not None else None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_book_endpoint(
    book: BookCreate,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, int]:
    try:
        book_id = await create_book(
            connection,
            book.title,
            book.isbn,
            book.publisher_id,
            book.genre,
            book.publication_date,
        )
    except oracledb.DatabaseError as error:
        if _database_error_code(error) == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A book with this ISBN already exists",
            ) from error
        if _database_error_code(error) == 2291:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="publisher_id does not exist",
            ) from error
        raise
    return {"book_id": book_id}


@router.post("/{book_id}/copies", status_code=status.HTTP_201_CREATED)
async def create_book_copy(
    book_id: int,
    copy: BookCopyCreate,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, int]:
    try:
        copy_id = await add_book_copy(connection, book_id, copy.shelf_location)
    except oracledb.DatabaseError as error:
        if _database_error_code(error) == 2291:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            ) from error
        raise
    return {"copy_id": copy_id}


@router.patch("/copies/{copy_id}/status")
async def set_copy_status(
    copy_id: int,
    update: CopyStatusUpdate,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, str]:
    if update.copy_status == "ON_LOAN":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use the loan checkout flow to mark a copy on loan",
        )
    updated = await update_copy_status(connection, copy_id, update.copy_status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Copy not found"
        )
    return {"message": "Copy status updated"}


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
