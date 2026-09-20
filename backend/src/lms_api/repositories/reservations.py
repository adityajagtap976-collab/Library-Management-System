from datetime import date
from typing import Any


async def create_reservation(
    connection: Any, member_id: int, book_id: int
) -> dict[str, Any]:
    cursor = await connection.cursor()
    try:
        reservation_id = cursor.var(int)
        reservation_date = cursor.var(date)
        await cursor.execute(
            """
            INSERT INTO reservations (member_id, book_id)
            VALUES (:member_id, :book_id)
            RETURNING reservation_id, reservation_date
            INTO :reservation_id, :reservation_date
            """,
            member_id=member_id,
            book_id=book_id,
            reservation_id=reservation_id,
            reservation_date=reservation_date,
        )
        await connection.commit()
        return {
            "reservation_id": int(reservation_id.getvalue()),
            "reservation_date": reservation_date.getvalue(),
            "reservation_status": "WAITING",
        }
    finally:
        await cursor.close()


async def cancel_reservation(
    connection: Any, reservation_id: int, member_id: int
) -> str:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT member_id
            FROM reservations
            WHERE reservation_id = :reservation_id
            """,
            reservation_id=reservation_id,
        )
        row = await cursor.fetchone()
        if row is None:
            return "not_found"
        if int(row[0]) != member_id:
            return "not_owned"

        await cursor.callproc(
            "cancel_reservation",
            [reservation_id, "Cancelled by member"],
        )
        await connection.commit()
        return "cancelled"
    finally:
        await cursor.close()


async def list_reservations_for_member(
    connection: Any, member_id: int, limit: int, offset: int
) -> list[dict[str, Any]]:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT r.reservation_id,
                   b.title,
                   b.isbn,
                   r.reservation_date,
                   r.reservation_status,
                   r.fulfilled_date
            FROM reservations r
            JOIN books b ON b.book_id = r.book_id
            WHERE r.member_id = :member_id
            ORDER BY r.reservation_date DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            member_id=member_id,
            limit=limit,
            offset=offset,
        )
        rows = await cursor.fetchall()
        return [
            {
                "reservation_id": row[0],
                "title": row[1],
                "isbn": row[2],
                "reservation_date": row[3],
                "reservation_status": row[4],
                "fulfilled_date": row[5],
            }
            for row in rows
        ]
    finally:
        await cursor.close()


async def count_reservations_for_member(connection: Any, member_id: int) -> int:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT COUNT(*)
            FROM reservations
            WHERE member_id = :member_id
            """,
            member_id=member_id,
        )
        row = await cursor.fetchone()
        return int(row[0])
    finally:
        await cursor.close()
