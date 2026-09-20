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


async def get_member_by_id(connection: Any, member_id: int) -> dict[str, Any] | None:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            SELECT member_id,
                   first_name,
                   last_name,
                   email,
                   phone,
                   member_status
            FROM members
            WHERE member_id = :member_id
            """,
            member_id=member_id,
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "member_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "phone": row[4],
            "member_status": row[5],
        }
    finally:
        await cursor.close()


async def create_member(
    connection: Any,
    first_name: str,
    last_name: str,
    email: str,
    password_hash: str,
) -> None:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            INSERT INTO members (first_name, last_name, email, password_hash)
            VALUES (:first_name, :last_name, :email, :password_hash)
            """,
            first_name=first_name,
            last_name=last_name,
            email=email.strip(),
            password_hash=password_hash,
        )
        await connection.commit()
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


async def update_member_contact_info(
    connection: Any,
    member_id: int,
    first_name: str,
    last_name: str,
    phone: str | None,
) -> bool:
    cursor = await connection.cursor()
    try:
        await cursor.execute(
            """
            UPDATE members
            SET first_name = :first_name,
                last_name = :last_name,
                phone = :phone
            WHERE member_id = :member_id
            """,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            member_id=member_id,
        )
        await connection.commit()
        return bool(cursor.rowcount > 0)
    finally:
        await cursor.close()
