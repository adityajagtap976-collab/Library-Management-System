from datetime import date
from typing import Any


async def create_book(
    connection: Any,
    title: str,
    isbn: str,
    publisher_id: int,
    genre: str | None,
    publication_date: date | None,
) -> int:
    cursor = await connection.cursor()
    try:
        book_id = cursor.var(int)
        await cursor.execute(
            """
            INSERT INTO books (
                title, isbn, publisher_id, genre, publication_date
            ) VALUES (
                :title, :isbn, :publisher_id, :genre, :publication_date
            )
            RETURNING book_id INTO :book_id
            """,
            title=title,
            isbn=isbn,
            publisher_id=publisher_id,
            genre=genre,
            publication_date=publication_date,
            book_id=book_id,
        )
        await connection.commit()
        return int(book_id.getvalue())
    finally:
        await cursor.close()


async def add_book_copy(
    connection: Any, book_id: int, shelf_location: str | None
) -> int:
    cursor = await connection.cursor()
    try:
        copy_id = cursor.var(int)
        await cursor.execute(
            """
            INSERT INTO book_copies (book_id, shelf_location)
            VALUES (:book_id, :shelf_location)
            RETURNING copy_id INTO :copy_id
            """,
            book_id=book_id,
            shelf_location=shelf_location,
            copy_id=copy_id,
        )
        await connection.commit()
        return int(copy_id.getvalue())
    finally:
        await cursor.close()


async def update_copy_status(connection: Any, copy_id: int, new_status: str) -> bool:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            UPDATE book_copies
            SET copy_status = :new_status
            WHERE copy_id = :copy_id
            """,
            new_status=new_status,
            copy_id=copy_id,
        )
        if cursor.rowcount == 0:
            return False
        await connection.commit()
        return True
    finally:
        await cursor.close()


async def list_books(connection: Any, limit: int, offset: int) -> list[dict[str, Any]]:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT b.book_id,
                   b.title,
                   b.isbn,
                   p.publisher_name,
                   (
                       SELECT LISTAGG(
                                  a.first_name || ' ' || a.last_name,
                                  ', '
                              ) WITHIN GROUP (ORDER BY a.last_name, a.first_name)
                       FROM book_authors ba
                       JOIN authors a ON a.author_id = ba.author_id
                       WHERE ba.book_id = b.book_id
                   ),
                   b.genre
            FROM books b
            JOIN publishers p ON p.publisher_id = b.publisher_id
            GROUP BY b.book_id,
                     b.title,
                     b.isbn,
                     p.publisher_name,
                     b.genre
            ORDER BY b.book_id
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            limit=limit,
            offset=offset,
        )
        rows = await cursor.fetchall()
        return [_book_summary_from_row(row) for row in rows]
    finally:
        await cursor.close()


async def get_book_by_id(connection: Any, book_id: int) -> dict[str, Any] | None:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT b.book_id,
                   b.title,
                   b.isbn,
                   p.publisher_name,
                   (
                       SELECT LISTAGG(
                                  a.first_name || ' ' || a.last_name,
                                  ', '
                              ) WITHIN GROUP (ORDER BY a.last_name, a.first_name)
                       FROM book_authors ba
                       JOIN authors a ON a.author_id = ba.author_id
                       WHERE ba.book_id = b.book_id
                   ),
                   b.genre,
                   c.copy_id,
                   c.copy_status,
                   c.shelf_location
            FROM books b
            JOIN publishers p ON p.publisher_id = b.publisher_id
            LEFT JOIN book_copies c ON c.book_id = b.book_id
            WHERE b.book_id = :book_id
            ORDER BY c.copy_id
            """,
            book_id=book_id,
        )
        rows = await cursor.fetchall()
        if not rows:
            return None

        first_row = rows[0]
        copies = [
            {
                "copy_id": row[6],
                "copy_status": row[7],
                "shelf_location": row[8],
            }
            for row in rows
            if row[6] is not None
        ]
        summary = _book_summary_from_row(first_row)
        return {**summary, "copies": copies}
    finally:
        await cursor.close()


async def count_books(connection: Any) -> int:
    cursor = await connection.cursor()
    try:
        await cursor.execute("SELECT COUNT(*) FROM books")
        row = await cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        await cursor.close()


def _book_summary_from_row(row: Any) -> dict[str, Any]:
    authors = row[4].split(", ") if row[4] else []
    return {
        "book_id": row[0],
        "title": row[1],
        "isbn": row[2],
        "publisher_name": row[3],
        "authors": authors,
        "genre": row[5],
    }
