from collections.abc import Sequence
from datetime import date
from typing import cast

import jwt
import oracledb
import pytest
from lms_api.core import security
from lms_api.routers import auth


class FakeCursor:
    def __init__(
        self,
        rows: Sequence[tuple[object, ...]] | None = None,
        fetchone_result: tuple[object, ...] | None = None,
        returning_value: int = 1,
        returning_due_date: date = date(2026, 10, 3),
        returning_return_date: date = date(2026, 9, 19),
        copy_status: str = "AVAILABLE",
        execute_error: Exception | None = None,
        rowcount: int = 1,
        rows_by_member_id: dict[int, Sequence[tuple[object, ...]]] | None = None,
    ) -> None:
        self.executed: tuple[str, dict[str, object]] | None = None
        self.executed_statements: list[tuple[str, dict[str, object]]] = []
        self.rows = list(rows or [])
        self.fetchone_result = fetchone_result
        self.returning_value = returning_value
        self.returning_due_date = returning_due_date
        self.returning_return_date = returning_return_date
        self.copy_status = copy_status
        self.rows_by_member_id = rows_by_member_id or {}
        self.date_variables: list[FakeVariable] = []
        self.execute_error = execute_error
        self.rowcount = rowcount

    def var(self, value_type: type[object]) -> "FakeVariable":
        value: object
        if value_type is int:
            value = self.returning_value
        else:
            value = self.returning_due_date
        variable = FakeVariable(value)
        if value_type is not int:
            self.date_variables.append(variable)
        return variable

    async def execute(self, statement: str, **parameters: object) -> None:
        if self.execute_error is not None:
            raise self.execute_error
        self.executed = (statement, parameters)
        self.executed_statements.append((statement, parameters))
        if "WHERE l.member_id = :member_id" in statement:
            member_id = cast(int, parameters["member_id"])
            self.rows = list(self.rows_by_member_id.get(member_id, self.rows))
        if "UPDATE loans" in statement:
            self.date_variables[-1].value = self.returning_return_date
        if "SELECT copy_status" in statement:
            self.fetchone_result = (self.copy_status,)

    async def fetchone(self) -> tuple[object, ...] | None:
        return self.fetchone_result

    async def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows

    async def close(self) -> None:
        pass


class FakeConnection:
    def __init__(
        self,
        rows: Sequence[tuple[object, ...]] | None = None,
        fetchone_result: tuple[object, ...] | None = None,
        returning_value: int = 1,
        returning_due_date: date = date(2026, 10, 3),
        returning_return_date: date = date(2026, 9, 19),
        copy_status: str = "AVAILABLE",
        execute_error: Exception | None = None,
        rowcount: int = 1,
        rows_by_member_id: dict[int, Sequence[tuple[object, ...]]] | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            fetchone_result,
            returning_value,
            returning_due_date,
            returning_return_date,
            copy_status,
            execute_error,
            rowcount,
            rows_by_member_id,
        )
        self.commits = 0

    async def cursor(self) -> FakeCursor:
        return self.cursor_instance

    async def commit(self) -> None:
        self.commits += 1


class FakeVariable:
    def __init__(self, value: object) -> None:
        self.value = value

    def getvalue(self) -> object:
        return self.value


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
    assert claims["role"] == "member"
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


@pytest.mark.anyio
async def test_staff_login_returns_staff_role_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    password_hash = security.hash_password("correct horse battery staple")

    async def find_staff(_connection: object, _email: str) -> dict[str, object]:
        return _staff(password_hash)

    monkeypatch.setattr(auth, "find_staff_by_email", find_staff)

    response = await auth.staff_login(
        auth.Credentials(
            email="admin@test.com",
            password="correct horse battery staple",
        ),
        cast(oracledb.AsyncConnection, FakeConnection()),
    )

    claims = jwt.decode(
        response["access_token"],
        "test-secret-with-at-least-32-bytes",
        algorithms=["HS256"],
    )
    assert claims["sub"] == "7"
    assert claims["email"] == "admin@test.com"
    assert claims["role"] == "staff"


@pytest.mark.anyio
async def test_staff_login_rejects_wrong_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password_hash = security.hash_password("correct horse battery staple")

    async def find_staff(_connection: object, _email: str) -> dict[str, object]:
        return _staff(password_hash)

    monkeypatch.setattr(auth, "find_staff_by_email", find_staff)

    with pytest.raises(auth.HTTPException) as error:
        await auth.staff_login(
            auth.Credentials(email="admin@test.com", password="wrong-password"),
            cast(oracledb.AsyncConnection, FakeConnection()),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid credentials"


@pytest.mark.anyio
async def test_staff_login_rejects_inactive_staff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password_hash = security.hash_password("correct horse battery staple")

    async def find_staff(_connection: object, _email: str) -> dict[str, object]:
        return _staff(password_hash, is_active="N")

    monkeypatch.setattr(auth, "find_staff_by_email", find_staff)

    with pytest.raises(auth.HTTPException) as error:
        await auth.staff_login(
            auth.Credentials(
                email="inactive@test.com",
                password="correct horse battery staple",
            ),
            cast(oracledb.AsyncConnection, FakeConnection()),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid credentials"


@pytest.mark.anyio
async def test_staff_login_verifies_dummy_hash_for_unknown_staff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_hashes: list[str] = []

    async def no_staff(_connection: object, _email: str) -> None:
        return None

    def capture_verification(password: str, password_hash: str) -> bool:
        captured_hashes.append(password_hash)
        return False

    monkeypatch.setattr(auth, "find_staff_by_email", no_staff)
    monkeypatch.setattr(auth, "verify_password", capture_verification)

    with pytest.raises(auth.HTTPException) as error:
        await auth.staff_login(
            auth.Credentials(email="missing-staff@test.com", password="password123"),
            cast(oracledb.AsyncConnection, FakeConnection()),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid credentials"
    assert captured_hashes == [security.DUMMY_PASSWORD_HASH]


def _member(password_hash: str) -> dict[str, object]:
    return {"member_id": 42, "email": "alice@test.com", "password_hash": password_hash}


def _staff(password_hash: str, is_active: str = "Y") -> dict[str, object]:
    return {
        "staff_id": 7,
        "email": "admin@test.com",
        "password_hash": password_hash,
        "is_active": is_active,
    }
