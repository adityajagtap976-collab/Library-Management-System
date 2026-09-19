from datetime import UTC, date, datetime
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
        await cursor.execute(
            """
            UPDATE loans
            SET return_date = SYSDATE
            WHERE loan_id = :loan_id
              AND return_date IS NULL
            RETURNING copy_id INTO :copy_id
            """,
            loan_id=loan_id,
            copy_id=copy_id,
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
            "return_date": datetime.now(UTC).date(),
            "copy_status": row[0],
        }
    finally:
        await cursor.close()
