import os
from datetime import UTC, datetime, timedelta
from typing import Literal, cast

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)
MAX_PASSWORD_LEN = 128
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$yk0IBS3hb9IYJNnfjg/txg$"
    "sjGf0RyFaYPA0trV0I4J5tRH4K6ZKJre80A/AlfwyAs"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30


def _get_jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a value of at least 32 bytes - "
            "refusing to start with an insecure default"
        )
    return secret


JWT_SECRET = _get_jwt_secret()


def hash_password(password: str) -> str:
    if not password or len(password) > MAX_PASSWORD_LEN:
        raise ValueError("invalid password length")
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return password_hasher.check_needs_rehash(password_hash)


def create_access_token(
    subject_id: int, email: str, role: Literal["member", "staff"]
) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject_id),
        "email": email,
        "role": role,
        "exp": expires_at,
    }
    return cast(str, jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM))
