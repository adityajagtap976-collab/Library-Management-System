from collections.abc import AsyncIterator
from typing import Literal, cast

import httpx
import pytest
from lms_api.core.security import create_access_token
from lms_api.db.session import get_connection
from lms_api.main import app
from lms_api.repositories.catalog import count_books, get_book_by_id, list_books

from tests.test_auth import FakeConnection

BOOK_ROWS = [
    (1, "Dune", "9780441013593", "Ace Books", "Frank Herbert", "Science Fiction"),
    (2, "Foundation", "9780553293357", "Bantam", "Isaac Asimov", "Science Fiction"),
]
DETAIL_ROWS = [
    (
        1,
        "Dune",
        "9780441013593",
        "Ace Books",
        "Frank Herbert",
        "Science Fiction",
        10,
        "AVAILABLE",
        "A-01",
    ),
    (
        1,
        "Dune",
        "9780441013593",
        "Ace Books",
        "Frank Herbert",
        "Science Fiction",
        11,
        "ON_LOAN",
        "A-02",
    ),
]


@pytest.mark.anyio
async def test_catalog_repositories_use_canned_rows_and_pagination() -> None:
    connection = FakeConnection(rows=BOOK_ROWS)

    books = await list_books(connection, limit=20, offset=40)

    assert books == [
        {
            "book_id": 1,
            "title": "Dune",
            "isbn": "9780441013593",
            "publisher_name": "Ace Books",
            "authors": ["Frank Herbert"],
            "genre": "Science Fiction",
        },
        {
            "book_id": 2,
            "title": "Foundation",
            "isbn": "9780553293357",
            "publisher_name": "Bantam",
            "authors": ["Isaac Asimov"],
            "genre": "Science Fiction",
        },
    ]
    assert connection.cursor_instance.executed is not None
    statement, parameters = connection.cursor_instance.executed
    assert "OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY" in statement
    assert parameters == {"limit": 20, "offset": 40}


@pytest.mark.anyio
async def test_get_book_by_id_nests_copies_from_one_result_set() -> None:
    connection = FakeConnection(rows=DETAIL_ROWS)

    book = await get_book_by_id(connection, 1)

    assert book == {
        "book_id": 1,
        "title": "Dune",
        "isbn": "9780441013593",
        "publisher_name": "Ace Books",
        "authors": ["Frank Herbert"],
        "genre": "Science Fiction",
        "copies": [
            {"copy_id": 10, "copy_status": "AVAILABLE", "shelf_location": "A-01"},
            {"copy_id": 11, "copy_status": "ON_LOAN", "shelf_location": "A-02"},
        ],
    }


@pytest.mark.anyio
async def test_count_books_uses_count_query() -> None:
    connection = FakeConnection(fetchone_result=(37,))

    total = await count_books(connection)

    assert total == 37


@pytest.mark.anyio
async def test_books_requires_authentication() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/books")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_members_and_staff_can_browse_books() -> None:
    app.dependency_overrides[get_connection] = _connection_override
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            member_response = await client.get(
                "/books",
                headers={"Authorization": _authorization("member")},
            )
            staff_response = await client.get(
                "/books",
                headers={"Authorization": _authorization("staff")},
            )
    finally:
        app.dependency_overrides.clear()

    assert member_response.status_code == 200
    assert staff_response.status_code == 200
    assert member_response.json()["items"][0]["title"] == "Dune"


@pytest.mark.anyio
async def test_books_limit_is_capped_by_query_validation() -> None:
    app.dependency_overrides[get_connection] = _connection_override
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/books?limit=500",
                headers={"Authorization": _authorization("member")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_book_returns_404() -> None:
    async def empty_connection() -> AsyncIterator[FakeConnection]:
        yield FakeConnection(rows=[])

    app.dependency_overrides[get_connection] = empty_connection
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/books/999",
                headers={"Authorization": _authorization("member")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


async def _connection_override() -> AsyncIterator[FakeConnection]:
    yield FakeConnection(rows=BOOK_ROWS, fetchone_result=(2,))


def _authorization(role: str) -> str:
    token = create_access_token(
        42,
        f"{role}@test.com",
        role=cast(Literal["member", "staff"], role),
    )
    return f"Bearer {token}"
