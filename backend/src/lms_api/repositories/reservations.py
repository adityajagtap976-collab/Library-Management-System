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
