from typing import cast

import oracledb
from fastapi import APIRouter, Depends, HTTPException, status

from lms_api.core.dependencies import Principal, require_role
from lms_api.db.session import get_connection
from lms_api.models.reservations import ReservationCreate, ReservationCreated
from lms_api.repositories.reservations import (
    cancel_reservation,
    create_reservation,
)

router = APIRouter(prefix="/reservations")


def _database_error_details(error: oracledb.DatabaseError) -> tuple[int | None, str]:
    database_error = error.args[0] if error.args else None
    code = getattr(database_error, "code", None)
    message = getattr(database_error, "message", "")
    return (int(code) if code is not None else None, str(message))


@router.post("", response_model=ReservationCreated, status_code=status.HTTP_201_CREATED)
async def create_reservation_endpoint(
    reservation: ReservationCreate,
    principal: Principal = Depends(require_role("member")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> ReservationCreated:
    member_id = int(cast(str, principal["sub"]))
    try:
        created_reservation = await create_reservation(
            connection, member_id, reservation.book_id
        )
    except oracledb.DatabaseError as error:
        code, message = _database_error_details(error)
        if code == 20003:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Copies are currently available — borrow directly instead "
                    "of reserving"
                ),
            ) from error
        if code == 2291 and "FK_RES_BOOK" in message.upper():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            ) from error
        if code == 1 and "UQ_RES_ACTIVE_MEMBER_BOOK" in message.upper():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a reservation for this book in this status",
            ) from error
        raise
    return ReservationCreated(**created_reservation)


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    principal: Principal = Depends(require_role("member")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> None:
    member_id = int(cast(str, principal["sub"]))
    try:
        outcome = await cancel_reservation(connection, reservation_id, member_id)
    except oracledb.DatabaseError:  # noqa: TRY203
        raise

    if outcome == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    if outcome == "not_owned":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
