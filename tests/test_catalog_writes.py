from collections.abc import AsyncIterator, Callable

import httpx
import oracledb
import pytest
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection
from tests.test_catalog import _authorization


def _database_error(code: int) -> oracledb.DatabaseError:
    error_info = type("OracleError", (), {"code": code})()
    return oracledb.DatabaseError(error_info)


@pytest.mark.anyio
async def test_staff_can_create_book() -> None:
    app.dependency_overrides[get_connection] = _write_connection(returning_value=123)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/books",
                json={
                    "title": "Dune",
                    "isbn": "9780441013593",
                    "publisher_id": 4,
                    "genre": "Science Fiction",
                    "publication_date": "1965-08-01",
                },
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {"book_id": 123}


@pytest.mark.anyio
async def test_member_cannot_create_book() -> None:
    app.dependency_overrides[get_connection] = _write_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/books",
                json={"title": "Dune", "isbn": "9780441013593", "publisher_id": 4},
                headers={"Authorization": _authorization("member")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error_code", "expected_status", "expected_detail"),
    [
        (1, 409, "A book with this ISBN already exists"),
        (2291, 422, "publisher_id does not exist"),
    ],
)
async def test_create_book_maps_database_errors(
    error_code: int, expected_status: int, expected_detail: str
) -> None:
    app.dependency_overrides[get_connection] = _write_connection(
        execute_error=_database_error(error_code)
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/books",
                json={"title": "Dune", "isbn": "9780441013593", "publisher_id": 4},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


@pytest.mark.anyio
async def test_copy_creation_maps_missing_book_to_404() -> None:
    app.dependency_overrides[get_connection] = _write_connection(
        execute_error=_database_error(2291)
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/books/999/copies",
                json={"shelf_location": "A-01"},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


@pytest.mark.anyio
async def test_copy_status_rejects_direct_on_loan_transition() -> None:
    app.dependency_overrides[get_connection] = _write_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/books/copies/10/status",
                json={"copy_status": "ON_LOAN"},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Use the loan checkout flow to mark a copy on loan"
    )


@pytest.mark.anyio
async def test_missing_copy_status_update_returns_404() -> None:
    app.dependency_overrides[get_connection] = _write_connection(rowcount=0)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/books/copies/999/status",
                json={"copy_status": "LOST"},
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Copy not found"


def _write_connection(
    returning_value: int = 1,
    execute_error: Exception | None = None,
    rowcount: int = 1,
) -> Callable[[], AsyncIterator[FakeConnection]]:
    async def override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            returning_value=returning_value,
            execute_error=execute_error,
            rowcount=rowcount,
        )

    return override
