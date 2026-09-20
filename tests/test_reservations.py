from collections.abc import AsyncIterator, Callable
from datetime import date

import httpx
import oracledb
import pytest
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection
from tests.test_loans import _member_authorization


def _database_error(code: int, message: str) -> oracledb.DatabaseError:
    error_info = type("OracleError", (), {"code": code, "message": message})()
    return oracledb.DatabaseError(error_info)


def _connection_override(
    *,
    execute_error: Exception | None = None,
    fetchone_result: tuple[object, ...] | None = (7,),
) -> Callable[[], AsyncIterator[FakeConnection]]:
    async def override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            returning_value=501,
            returning_due_date=date(2026, 9, 19),
            execute_error=execute_error,
            fetchone_result=fetchone_result,
        )

    return override


@pytest.mark.anyio
async def test_member_can_create_reservation() -> None:
    app.dependency_overrides[get_connection] = _connection_override()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/reservations",
                json={"book_id": 42},
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "reservation_id": 501,
        "reservation_date": "2026-09-19",
        "reservation_status": "WAITING",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (
            _database_error(20003, "ORA-20003: copies available"),
            409,
            "Copies are currently available — borrow directly instead of reserving",
        ),
        (
            _database_error(
                2291,
                "ORA-02291: integrity constraint (LMS.FK_RES_BOOK) violated",
            ),
            404,
            "Book not found",
        ),
        (
            _database_error(
                1,
                "ORA-00001: unique constraint (LMS.UQ_RES_ACTIVE_MEMBER_BOOK) violated",
            ),
            409,
            "You already have a reservation for this book in this status",
        ),
    ],
)
async def test_create_reservation_maps_database_errors(
    error: oracledb.DatabaseError, expected_status: int, expected_detail: str
) -> None:
    app.dependency_overrides[get_connection] = _connection_override(execute_error=error)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/reservations",
                json={"book_id": 42},
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


@pytest.mark.anyio
async def test_member_can_cancel_own_reservation() -> None:
    app.dependency_overrides[get_connection] = _connection_override(
        fetchone_result=(7,)
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/reservations/501",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204


@pytest.mark.anyio
async def test_member_cannot_cancel_someone_elses_reservation() -> None:
    app.dependency_overrides[get_connection] = _connection_override(
        fetchone_result=(8,)
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/reservations/501",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_member_cannot_cancel_missing_reservation() -> None:
    app.dependency_overrides[get_connection] = _connection_override(
        fetchone_result=None
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/reservations/999",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.anyio
async def test_member_can_complete_two_reserve_cancel_cycles() -> None:
    app.dependency_overrides[get_connection] = _connection_override(
        fetchone_result=(7,)
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            headers = {"Authorization": _member_authorization(7)}
            first_create = await client.post(
                "/reservations", json={"book_id": 42}, headers=headers
            )
            first_cancel = await client.delete("/reservations/501", headers=headers)
            second_create = await client.post(
                "/reservations", json={"book_id": 42}, headers=headers
            )
            second_cancel = await client.delete("/reservations/501", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert first_create.status_code == 201
    assert first_cancel.status_code == 204
    assert second_create.status_code == 201
    assert second_cancel.status_code == 204
