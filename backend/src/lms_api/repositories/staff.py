from typing import Any


async def find_staff_by_email(connection: Any, email: str) -> dict[str, Any] | None:
    normalized_email = email.strip().lower()
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT staff_id, email, password_hash, is_active
            FROM staff
            WHERE LOWER(email) = LOWER(:email)
            """,
            email=normalized_email,
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "staff_id": row[0],
            "email": row[1],
            "password_hash": row[2],
            "is_active": row[3],
        }
    finally:
        await cursor.close()
