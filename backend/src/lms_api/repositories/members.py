from typing import Any


async def find_member_by_email(connection: Any, email: str) -> dict[str, Any] | None:
    normalized_email = email.strip().lower()
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT member_id, email, password_hash
            FROM members
            WHERE LOWER(email) = LOWER(:email)
            """,
            email=normalized_email,
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {"member_id": row[0], "email": row[1], "password_hash": row[2]}
    finally:
        await cursor.close()


async def update_member_password_hash(
    connection: Any, member_id: int, password_hash: str
) -> None:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            UPDATE members
            SET password_hash = :password_hash
            WHERE member_id = :member_id
            """,
            password_hash=password_hash,
            member_id=member_id,
        )
        await connection.commit()
    finally:
        await cursor.close()
