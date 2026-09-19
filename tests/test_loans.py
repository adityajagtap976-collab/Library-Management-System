from collections.abc import AsyncIterator, Callable
from datetime import UTC, date, datetime

import httpx
import oracledb
import pytest
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection
from tests.test_catalog import _authorization


def _database_error(code: int, message: str) -> oracledb.DatabaseError:
    error_info = type("OracleError", (), {"code": code, "message": message})()
    return oracledb.DatabaseError(error_info)


@pytest.mark.anyio
async def test_staff_can_create_loan() -> None:
    app.dependency_overrides[get_connection] = _loan_connection(
        returning_value=123,
        returning_due_date=date(2026, 10, 3),
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/loans",
                json={"member_id": 7, "copy_id": 42},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {"loan_id": 123, "due_date": "2026-10-03"}


@pytest.mark.anyio
async def test_member_cannot_create_loan() -> None:
    app.dependency_overrides[get_connection] = _loan_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/loans",
                json={"member_id": 7, "copy_id": 42},
                headers={"Authorization": _authorization("member")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_detail"),
    [
        (
            _database_error(20004, "ORA-20004: copy is unavailable"),
            "Copy is not available for loan",
        ),
        (
            _database_error(20005, "ORA-20005: member is suspended"),
            "Member is not active and cannot check out books",
        ),
    ],
)
async def test_create_loan_maps_business_errors(
    error: oracledb.DatabaseError, expected_detail: str
) -> None:
    app.dependency_overrides[get_connection] = _loan_connection(execute_error=error)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/loans",
                json={"member_id": 7, "copy_id": 42},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == expected_detail


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("constraint_name", "expected_detail"),
    [("FK_LOANS_COPY", "Copy not found"), ("FK_LOANS_MEMBER", "Member not found")],
)
# This validates router mapping only, not the trigger's behavior against real Oracle.
async def test_create_loan_maps_missing_references(
    constraint_name: str, expected_detail: str
) -> None:
    error = _database_error(
        2291,
        f"ORA-02291: integrity constraint (LMS.{constraint_name}) violated",
    )
    app.dependency_overrides[get_connection] = _loan_connection(execute_error=error)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/loans",
                json={"member_id": 7, "copy_id": 42},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail


@pytest.mark.anyio
async def test_unrecognized_loan_foreign_key_error_is_not_swallowed() -> None:
    error = _database_error(2291, "ORA-02291: unrelated constraint violated")
    app.dependency_overrides[get_connection] = _loan_connection(execute_error=error)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/loans",
                json={"member_id": 7, "copy_id": 42},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500


@pytest.mark.anyio
@pytest.mark.parametrize("copy_status", ["AVAILABLE", "ON_LOAN"])
async def test_staff_can_return_loan(copy_status: str) -> None:
    app.dependency_overrides[get_connection] = _loan_connection(
        copy_status=copy_status,
        rowcount=1,
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/loans/123/return",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "loan_id": 123,
        "return_date": datetime.now(UTC).date().isoformat(),
        "copy_status": copy_status,
    }


@pytest.mark.anyio
async def test_returning_nonexistent_loan_returns_404() -> None:
    app.dependency_overrides[get_connection] = _loan_connection(
        fetchone_result=None,
        rowcount=0,
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/loans/999/return",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Loan not found"


@pytest.mark.anyio
async def test_returning_already_returned_loan_returns_prior_date() -> None:
    prior_return_date = date(2026, 9, 18)
    app.dependency_overrides[get_connection] = _loan_connection(
        fetchone_result=(prior_return_date,),
        rowcount=0,
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/loans/123/return",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == (
        f"Loan was already returned on {prior_return_date}"
    )


@pytest.mark.anyio
async def test_member_cannot_return_loan() -> None:
    app.dependency_overrides[get_connection] = _loan_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/loans/123/return",
                headers={"Authorization": _authorization("member")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def _loan_connection(
    returning_value: int = 1,
    returning_due_date: date = date(2026, 10, 3),
    copy_status: str = "AVAILABLE",
    fetchone_result: tuple[object, ...] | None = ("AVAILABLE",),
    rowcount: int = 1,
    execute_error: Exception | None = None,
) -> Callable[[], AsyncIterator[FakeConnection]]:
    async def override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            returning_value=returning_value,
            returning_due_date=returning_due_date,
            copy_status=copy_status,
            fetchone_result=fetchone_result,
            rowcount=rowcount,
            execute_error=execute_error,
        )

    return override
