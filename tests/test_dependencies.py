from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from fastapi import HTTPException
from lms_api.core.dependencies import get_current_principal, require_role
from lms_api.core.security import (
    JWT_ALGORITHM,
    JWT_SECRET,
    create_access_token,
)
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection


@pytest.mark.anyio
async def test_get_current_principal_returns_valid_member_payload() -> None:
    token = create_access_token(42, "member@test.com", role="member")

    principal = await get_current_principal(token)

    assert principal["sub"] == "42"
    assert principal["email"] == "member@test.com"
    assert principal["role"] == "member"


@pytest.mark.anyio
async def test_get_current_principal_rejects_expired_token() -> None:
    token = jwt.encode(
        {
            "sub": "42",
            "email": "member@test.com",
            "role": "member",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as error:
        await get_current_principal(token)

    assert error.value.status_code == 401
    assert error.value.detail == "Token expired"


@pytest.mark.anyio
async def test_get_current_principal_rejects_wrong_secret() -> None:
    token = jwt.encode(
        {"sub": "42", "email": "member@test.com", "role": "member"},
        "wrong-secret-with-at-least-32-bytes",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as error:
        await get_current_principal(token)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid token"


@pytest.mark.anyio
async def test_get_current_principal_rejects_malformed_token() -> None:
    with pytest.raises(HTTPException) as error:
        await get_current_principal("not-a-jwt")

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid token"


@pytest.mark.anyio
async def test_require_role_rejects_member_for_staff_role() -> None:
    principal = {"sub": "42", "email": "member@test.com", "role": "member"}

    with pytest.raises(HTTPException) as error:
        await require_role("staff")(principal)

    assert error.value.status_code == 403
    assert error.value.detail == "Forbidden"


@pytest.mark.anyio
async def test_require_role_passes_through_matching_member_role() -> None:
    principal = {"sub": "42", "email": "member@test.com", "role": "member"}

    result = await require_role("member")(principal)

    assert result is principal


@pytest.mark.anyio
async def test_protected_me_routes_enforce_roles() -> None:
    member_token = create_access_token(42, "member@test.com", role="member")
    staff_token = create_access_token(7, "staff@test.com", role="staff")

    async def connection_override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            member_profiles={
                42: (42, "Alice", "Borrower", "member@test.com", None, "ACTIVE")
            }
        )

    app.dependency_overrides[get_connection] = connection_override
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            member_response = await client.get(
                "/members/me",
                headers={"Authorization": f"Bearer {member_token}"},
            )
            member_staff_response = await client.get(
                "/staff/me",
                headers={"Authorization": f"Bearer {member_token}"},
            )
            staff_response = await client.get(
                "/staff/me",
                headers={"Authorization": f"Bearer {staff_token}"},
            )
            staff_member_response = await client.get(
                "/members/me",
                headers={"Authorization": f"Bearer {staff_token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert member_response.status_code == 200
    assert member_response.json()["member_id"] == 42
    assert member_response.json()["email"] == "member@test.com"
    assert member_staff_response.status_code == 403
    assert staff_response.status_code == 200
    assert staff_response.json() == {"staff_id": "7", "email": "staff@test.com"}
    assert staff_member_response.status_code == 403
