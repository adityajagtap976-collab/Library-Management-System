from datetime import date
from typing import Any


async def create_loan(connection: Any, member_id: int, copy_id: int) -> dict[str, Any]:
    cursor = await connection.cursor()
    try:
        loan_id = cursor.var(int)
        due_date = cursor.var(date)
        await cursor.execute(
            """
            INSERT INTO loans (member_id, copy_id)
            VALUES (:member_id, :copy_id)
            RETURNING loan_id, due_date INTO :loan_id, :due_date
            """,
            member_id=member_id,
            copy_id=copy_id,
            loan_id=loan_id,
            due_date=due_date,
        )
        await connection.commit()
        return {
            "loan_id": int(loan_id.getvalue()),
            "due_date": due_date.getvalue(),
        }
    finally:
        await cursor.close()


async def mark_loan_returned(connection: Any, loan_id: int) -> dict[str, Any]:
    cursor = await connection.cursor()
    try:
        copy_id = cursor.var(int)
        return_date = cursor.var(date)
        await cursor.execute(
            """
            UPDATE loans
            SET return_date = SYSDATE
            WHERE loan_id = :loan_id
              AND return_date IS NULL
            RETURNING copy_id, return_date INTO :copy_id, :return_date
            """,
            loan_id=loan_id,
            copy_id=copy_id,
            return_date=return_date,
        )

        if cursor.rowcount == 0:
            await cursor.execute(
                """
                SELECT return_date
                FROM loans
                WHERE loan_id = :loan_id
                """,
                loan_id=loan_id,
            )
            row = await cursor.fetchone()
            if row is None:
                return {"outcome": "not_found"}
            return {"outcome": "already_returned", "return_date": row[0]}

        returned_copy_id = int(copy_id.getvalue())
        await connection.commit()
        await cursor.execute(
            """
            SELECT copy_status
            FROM book_copies
            WHERE copy_id = :copy_id
            """,
            copy_id=returned_copy_id,
        )
        row = await cursor.fetchone()
        return {
            "outcome": "returned",
            "return_date": return_date.getvalue(),
            "copy_status": row[0],
        }
    finally:
        await cursor.close()


async def list_loans_for_member(
    connection: Any, member_id: int, limit: int, offset: int
) -> list[dict[str, Any]]:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT l.loan_id,
                   b.title,
                   b.isbn,
                   l.checkout_date,
                   l.due_date,
                   l.return_date,
                   CASE
                       WHEN l.return_date IS NULL AND l.due_date < SYSDATE THEN 1
                       ELSE 0
                   END AS is_overdue
            FROM loans l
            JOIN book_copies c ON c.copy_id = l.copy_id
            JOIN books b ON b.book_id = c.book_id
            WHERE l.member_id = :member_id
            ORDER BY l.checkout_date DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            member_id=member_id,
            limit=limit,
            offset=offset,
        )
        rows = await cursor.fetchall()
        return [
            {
                "loan_id": row[0],
                "title": row[1],
                "isbn": row[2],
                "checkout_date": row[3],
                "due_date": row[4],
                "return_date": row[5],
                "is_overdue": bool(row[6]),
            }
            for row in rows
        ]
    finally:
        await cursor.close()


async def count_loans_for_member(connection: Any, member_id: int) -> int:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT COUNT(*)
            FROM loans
            WHERE member_id = :member_id
            """,
            member_id=member_id,
        )
        row = await cursor.fetchone()
        return int(row[0])
    finally:
        await cursor.close()
