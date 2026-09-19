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
