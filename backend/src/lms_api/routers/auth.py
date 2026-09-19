import oracledb
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from lms_api.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from lms_api.db.session import get_connection
from lms_api.repositories.members import (
    create_member,
    find_member_by_email,
    update_member_password_hash,
)
from lms_api.repositories.staff import find_staff_by_email

router = APIRouter()


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupCredentials(Credentials):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    credentials: SignupCredentials,
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, str]:
    try:
        await create_member(
            connection,
            credentials.first_name.strip(),
            credentials.last_name.strip(),
            str(credentials.email),
            hash_password(credentials.password),
        )
    except oracledb.DatabaseError as error:
        database_error = error.args[0] if error.args else None
        if getattr(database_error, "code", None) == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A member with this email already exists",
            ) from error
        raise
    return {
        "email": str(credentials.email),
        "message": "Signup successful",
    }


@router.post("/login")
async def login(
    credentials: Credentials,
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, str]:
    member = await find_member_by_email(connection, str(credentials.email))
    stored_hash = member["password_hash"] if member else DUMMY_PASSWORD_HASH
    password_valid = verify_password(credentials.password, stored_hash)
    if member is None or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if password_needs_rehash(member["password_hash"]):
        await update_member_password_hash(
            connection,
            member["member_id"],
            hash_password(credentials.password),
        )
    return {
        "access_token": create_access_token(
            member["member_id"], member["email"], role="member"
        ),
        "token_type": "bearer",
    }


@router.post("/staff-login")
async def staff_login(
    credentials: Credentials,
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, str]:
    staff = await find_staff_by_email(connection, str(credentials.email))
    stored_hash = staff["password_hash"] if staff else DUMMY_PASSWORD_HASH
    password_valid = verify_password(credentials.password, stored_hash)
    if staff is None or staff["is_active"] != "Y" or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return {
        "access_token": create_access_token(
            staff["staff_id"], staff["email"], role="staff"
        ),
        "token_type": "bearer",
    }
