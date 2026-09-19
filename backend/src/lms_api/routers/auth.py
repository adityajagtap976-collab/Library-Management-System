import oracledb
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.src.lms_api.core.security import (
    hash_password,
    password_needs_rehash,
    verify_password,
)
from backend.src.lms_api.db.session import get_connection
from backend.src.lms_api.repositories.members import (
    find_member_by_email,
    update_member_password_hash,
)

router = APIRouter()


class Credentials(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(credentials: Credentials) -> dict[str, str]:
    return {
        "email": str(credentials.email),
        "password_hash": hash_password(credentials.password),
    }


@router.post("/login")
async def login(
    credentials: Credentials,
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> dict[str, str]:
    member = await find_member_by_email(connection, str(credentials.email))
    if member is None or not verify_password(
        credentials.password, member["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if password_needs_rehash(member["password_hash"]):
        await update_member_password_hash(
            connection,
            member["member_id"],
            hash_password(credentials.password),
        )
    return {"message": "Login successful"}
