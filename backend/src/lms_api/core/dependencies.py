from collections.abc import Awaitable, Callable
from typing import Literal, cast

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from lms_api.core.security import JWT_ALGORITHM, JWT_SECRET

Principal = dict[str, object]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_principal(token: str = Depends(oauth2_scheme)) -> Principal:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from error
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from error
    return cast(Principal, payload)


def require_role(
    role: Literal["member", "staff"],
) -> Callable[..., Awaitable[Principal]]:
    async def role_checker(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if principal.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
        return principal

    return role_checker
