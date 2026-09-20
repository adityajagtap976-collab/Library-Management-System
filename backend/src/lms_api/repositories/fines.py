from datetime import date
from typing import Any


async def generate_overdue_fines(connection: Any) -> int:
    cursor = await connection.cursor()
    try:
        await cursor.execute("SELECT COUNT(*) FROM fines")
        before = int((await cursor.fetchone())[0])
        await cursor.callproc("generate_overdue_fines", [])
        await cursor.execute("SELECT COUNT(*) FROM fines")
        after = int((await cursor.fetchone())[0])
        await connection.commit()
        return after - before
    finally:
        await cursor.close()


async def list_fines_for_member(
    connection: Any, member_id: int, limit: int, offset: int
) -> list[dict[str, Any]]:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT f.fine_id,
                   b.title,
                   f.fine_amount,
                   f.fine_reason,
                   f.issued_date,
                   f.paid_date,
                   CASE WHEN f.paid_date IS NOT NULL THEN 1 ELSE 0 END AS is_paid
            FROM fines f
            JOIN loans l ON l.loan_id = f.loan_id
            JOIN book_copies c ON c.copy_id = l.copy_id
            JOIN books b ON b.book_id = c.book_id
            WHERE l.member_id = :member_id
            ORDER BY f.issued_date DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            member_id=member_id,
            limit=limit,
            offset=offset,
        )
        rows = await cursor.fetchall()
        return [
            {
                "fine_id": row[0],
                "title": row[1],
                "fine_amount": row[2],
                "fine_reason": row[3],
                "issued_date": row[4],
                "paid_date": row[5],
                "is_paid": bool(row[6]),
            }
            for row in rows
        ]
    finally:
        await cursor.close()


async def count_fines_for_member(connection: Any, member_id: int) -> int:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT COUNT(*)
            FROM fines f
            JOIN loans l ON l.loan_id = f.loan_id
            WHERE l.member_id = :member_id
            """,
            member_id=member_id,
        )
        return int((await cursor.fetchone())[0])
    finally:
        await cursor.close()


async def mark_fine_paid(connection: Any, fine_id: int) -> dict[str, Any]:
    cursor = await connection.cursor()
    try:
        paid_date = cursor.var(date)
        await cursor.execute(
            """
            UPDATE fines
            SET paid_date = SYSDATE
            WHERE fine_id = :fine_id
              AND paid_date IS NULL
            RETURNING paid_date INTO :paid_date
            """,
            fine_id=fine_id,
            paid_date=paid_date,
        )
        if cursor.rowcount == 0:
            await cursor.execute(
                """
                SELECT paid_date
                FROM fines
                WHERE fine_id = :fine_id
                """,
                fine_id=fine_id,
            )
            row = await cursor.fetchone()
            if row is None:
                return {"outcome": "not_found"}
            return {"outcome": "already_paid", "paid_date": row[0]}

        await connection.commit()
        return {"outcome": "paid", "paid_date": paid_date.getvalue()}
    finally:
        await cursor.close()
