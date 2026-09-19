from typing import cast

import jwt
import oracledb
import pytest
from lms_api.core import security
from lms_api.routers import auth


class FakeCursor:
    def __init__(self) -> None:
        self.executed: tuple[str, dict[str, object]] | None = None

    async def execute(self, statement: str, **parameters: object) -> None:
        self.executed = (statement, parameters)

    async def fetchone(self) -> None:
        return None

    async def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.commits = 0

    async def cursor(self) -> FakeCursor:
        return self.cursor_instance

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.anyio
async def test_signup_inserts_member_without_returning_password_hash() -> None:
    connection = FakeConnection()

    response = await auth.signup(
        auth.SignupCredentials(
            first_name="Alice",
            last_name="Borrower",
            email=" Alice@Test.com ",
            password="correct horse battery staple",
        ),
        cast(oracledb.AsyncConnection, connection),
    )

    assert response == {"email": "Alice@test.com", "message": "Signup successful"}
    assert connection.commits == 1
    assert connection.cursor_instance.executed is not None
    _, parameters = connection.cursor_instance.executed
    assert parameters["email"] == "Alice@test.com"
    assert security.verify_password(
        "correct horse battery staple", str(parameters["password_hash"])
    )
    assert "password_hash" not in response


@pytest.mark.anyio
async def test_login_returns_signed_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    connection = FakeConnection()
    password_hash = security.hash_password("correct horse battery staple")

    async def find_member(_connection: object, _email: str) -> dict[str, object]:
        return _member(password_hash)

    monkeypatch.setattr(auth, "find_member_by_email", find_member)

    response = await auth.login(
        auth.Credentials(
            email="alice@test.com",
            password="correct horse battery staple",
        ),
        cast(oracledb.AsyncConnection, connection),
    )

    claims = jwt.decode(
        response["access_token"],
        "test-secret-with-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == "42"
    assert claims["email"] == "alice@test.com"
    assert response["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_verifies_dummy_hash_for_unknown_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_hashes: list[str] = []

    async def no_member(_connection: object, _email: str) -> None:
        return None

    def capture_verification(password: str, password_hash: str) -> bool:
        captured_hashes.append(password_hash)
        return False

    monkeypatch.setattr(auth, "find_member_by_email", no_member)
    monkeypatch.setattr(auth, "verify_password", capture_verification)

    with pytest.raises(auth.HTTPException) as error:
        await auth.login(
            auth.Credentials(email="missing@test.com", password="password123"),
            cast(oracledb.AsyncConnection, FakeConnection()),
        )

    assert error.value.status_code == 401
    assert captured_hashes == [security.DUMMY_PASSWORD_HASH]


def _member(password_hash: str) -> dict[str, object]:
    return {"member_id": 42, "email": "alice@test.com", "password_hash": password_hash}
