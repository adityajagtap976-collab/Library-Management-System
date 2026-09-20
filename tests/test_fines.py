from collections.abc import AsyncIterator, Callable, Sequence
from datetime import date
from typing import cast

import httpx
import oracledb
import pytest
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection
from tests.test_catalog import _authorization
from tests.test_loans import _member_authorization


def _database_error(code: int, message: str) -> oracledb.DatabaseError:
    error_info = type("OracleError", (), {"code": code, "message": message})()
    return oracledb.DatabaseError(error_info)


def _fine_connection(
    *,
    execute_error: Exception | None = None,
    fetchone_result: tuple[object, ...] | None = (1,),
    rows_by_member_id: dict[int, Sequence[tuple[object, ...]]] | None = None,
    count_results: Sequence[int] | None = None,
    returning_paid_date: date = date(2026, 9, 20),
    rowcount: int = 1,
) -> Callable[[], AsyncIterator[FakeConnection]]:
    async def override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            execute_error=execute_error,
            fetchone_result=fetchone_result,
            rows_by_member_id=rows_by_member_id,
            count_results=count_results,
            returning_paid_date=returning_paid_date,
            rowcount=rowcount,
        )

    return override


@pytest.mark.anyio
async def test_staff_can_generate_overdue_fines_from_count_difference() -> None:
    app.dependency_overrides[get_connection] = _fine_connection(count_results=[3, 5])
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/fines/generate-overdue",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"fines_created": 2}


@pytest.mark.anyio
async def test_member_cannot_generate_overdue_fines() -> None:
    app.dependency_overrides[get_connection] = _fine_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/fines/generate-overdue",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


FINE_ROWS = cast(
    dict[int, Sequence[tuple[object, ...]]],
    {
        7: [
            (101, "Dune", 10.0, "LATE_RETURN", date(2026, 9, 1), None, 0),
            (102, "Foundation", 25.0, "DAMAGED", date(2026, 9, 2), date(2026, 9, 3), 1),
        ],
        8: [(201, "1984", 15.0, "LOST", date(2026, 9, 4), None, 0)],
    },
)


@pytest.mark.anyio
async def test_member_can_list_own_fines_and_sql_paid_flag() -> None:
    app.dependency_overrides[get_connection] = _fine_connection(
        rows_by_member_id=FINE_ROWS,
        fetchone_result=(2,),
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/fines/mine?limit=10&offset=0",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "fine_id": 101,
            "title": "Dune",
            "fine_amount": 10.0,
            "fine_reason": "LATE_RETURN",
            "issued_date": "2026-09-01",
            "paid_date": None,
            "is_paid": False,
        },
        {
            "fine_id": 102,
            "title": "Foundation",
            "fine_amount": 25.0,
            "fine_reason": "DAMAGED",
            "issued_date": "2026-09-02",
            "paid_date": "2026-09-03",
            "is_paid": True,
        },
    ]


@pytest.mark.anyio
async def test_member_fine_history_binds_integer_subject_and_isolates_rows() -> None:
    connection = FakeConnection(rows_by_member_id=FINE_ROWS, fetchone_result=(2,))

    async def connection_override() -> AsyncIterator[FakeConnection]:
        yield connection

    app.dependency_overrides[get_connection] = connection_override
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/fines/mine",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    fine_query = next(
        parameters
        for statement, parameters in connection.cursor_instance.executed_statements
        if "WHERE l.member_id = :member_id" in statement
    )
    assert fine_query["member_id"] == 7


@pytest.mark.anyio
async def test_staff_cannot_list_member_fines() -> None:
    app.dependency_overrides[get_connection] = _fine_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/fines/mine?limit=500",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_staff_can_pay_fine_using_returned_database_date() -> None:
    database_paid_date = date(2026, 9, 21)
    app.dependency_overrides[get_connection] = _fine_connection(
        rowcount=1,
        returning_paid_date=database_paid_date,
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/fines/101/pay",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "fine_id": 101,
        "paid_date": database_paid_date.isoformat(),
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("fetchone_result", "expected_status", "expected_detail"),
    [
        ((date(2026, 9, 18),), 409, "Fine was already paid on 2026-09-18"),
        (None, 404, "Fine not found"),
    ],
)
async def test_staff_pay_fine_handles_missing_and_already_paid(
    fetchone_result: tuple[object, ...] | None,
    expected_status: int,
    expected_detail: str,
) -> None:
    app.dependency_overrides[get_connection] = _fine_connection(
        fetchone_result=fetchone_result,
        rowcount=0,
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/fines/101/pay",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


@pytest.mark.anyio
async def test_member_cannot_pay_fine() -> None:
    app.dependency_overrides[get_connection] = _fine_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/fines/101/pay",
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
