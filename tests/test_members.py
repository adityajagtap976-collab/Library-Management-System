from collections.abc import AsyncIterator, Callable, Sequence

import httpx
import pytest
from lms_api.db.session import get_connection
from lms_api.main import app

from tests.test_auth import FakeConnection
from tests.test_catalog import _authorization
from tests.test_fines import FINE_ROWS
from tests.test_loans import LOAN_ROWS, _member_authorization
from tests.test_reservations import RESERVATION_ROWS

MEMBER_PROFILE = (7, "Alice", "Borrower", "alice@test.com", "555-0100", "SUSPENDED")


def _member_connection(
    *,
    member_profile: tuple[object, ...] | None = MEMBER_PROFILE,
    rows_by_member_id: dict[int, Sequence[tuple[object, ...]]] | None = None,
    count_results: Sequence[int] | None = None,
) -> Callable[[], AsyncIterator[FakeConnection]]:
    async def override() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(
            member_profiles={7: member_profile} if member_profile else {},
            rows_by_member_id=rows_by_member_id,
            count_results=count_results,
        )

    return override


@pytest.mark.anyio
async def test_staff_can_get_member_profile() -> None:
    app.dependency_overrides[get_connection] = _member_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/members/7",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "member_id": 7,
        "first_name": "Alice",
        "last_name": "Borrower",
        "email": "alice@test.com",
        "phone": "555-0100",
        "member_status": "SUSPENDED",
    }


@pytest.mark.anyio
async def test_missing_member_profile_returns_404() -> None:
    app.dependency_overrides[get_connection] = _member_connection(member_profile=None)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/members/999",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


@pytest.mark.anyio
@pytest.mark.parametrize("resource", ["loans", "reservations", "fines"])
async def test_missing_member_subresource_returns_404(resource: str) -> None:
    app.dependency_overrides[get_connection] = _member_connection(member_profile=None)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/members/999/{resource}",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("resource", "rows", "count", "expected_id"),
    [
        ("loans", LOAN_ROWS, 2, 101),
        ("reservations", RESERVATION_ROWS, 3, 101),
        ("fines", FINE_ROWS, 2, 101),
    ],
)
async def test_staff_can_get_member_subresource(
    resource: str,
    rows: dict[int, Sequence[tuple[object, ...]]],
    count: int,
    expected_id: int,
) -> None:
    app.dependency_overrides[get_connection] = _member_connection(
        rows_by_member_id=rows,
        count_results=[count],
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/members/7/{resource}",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0][resource[:-1] + "_id"] == expected_id
    assert response.json()["total"] == count


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path",
    ["/members/7", "/members/7/loans", "/members/7/reservations", "/members/7/fines"],
)
async def test_member_token_cannot_access_staff_member_endpoints(path: str) -> None:
    app.dependency_overrides[get_connection] = _member_connection()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                path,
                headers={"Authorization": _member_authorization(7)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
