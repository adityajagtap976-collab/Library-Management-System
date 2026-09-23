from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lms_api.core.dependencies import Principal, require_role
from lms_api.core.security import hash_password, verify_password
from lms_api.db.session import get_connection
from lms_api.models.fines import FineHistoryEntry, PaginatedFines
from lms_api.models.loans import LoanHistoryEntry, PaginatedLoanHistory
from lms_api.models.members import MemberContactUpdate, MemberProfile, PasswordChange
from lms_api.models.reservations import (
    PaginatedReservations,
    ReservationHistoryEntry,
)
from lms_api.repositories.fines import count_fines_for_member, list_fines_for_member
from lms_api.repositories.loans import count_loans_for_member, list_loans_for_member
from lms_api.repositories.members import (
    get_member_by_id,
    get_member_password_hash,
    update_member_contact_info,
    update_member_password_hash,
)
from lms_api.repositories.reservations import (
    count_reservations_for_member,
    list_reservations_for_member,
)

router = APIRouter(prefix="/members")


async def _require_member(connection: Any, member_id: int) -> dict[str, Any]:
    member = await get_member_by_id(connection, member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    return member


@router.get("/me", response_model=MemberProfile)
async def get_my_member_profile(
    principal: Principal = Depends(require_role("member")),
    connection: Any = Depends(get_connection),
) -> MemberProfile:
    return MemberProfile(
        **await _require_member(connection, int(cast(str, principal["sub"])))
    )


@router.patch("/me", response_model=MemberProfile)
async def update_my_member_profile(
    update: MemberContactUpdate,
    principal: Principal = Depends(require_role("member")),
    connection: Any = Depends(get_connection),
) -> MemberProfile:
    member_id = int(cast(str, principal["sub"]))
    updated = await update_member_contact_info(
        connection,
        member_id,
        update.first_name,
        update.last_name,
        update.phone,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Member profile could not be updated",
        )
    return MemberProfile(**await _require_member(connection, member_id))


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    passwords: PasswordChange,
    principal: Principal = Depends(require_role("member")),
    connection: Any = Depends(get_connection),
) -> None:
    member_id = int(cast(str, principal["sub"]))
    stored_hash = await get_member_password_hash(connection, member_id)
    if stored_hash is None or not verify_password(
        passwords.current_password, stored_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current password is incorrect",
        )
    await update_member_password_hash(
        connection, member_id, hash_password(passwords.new_password)
    )


@router.get("/{member_id}", response_model=MemberProfile)
async def get_member_profile(
    member_id: int,
    _principal: Principal = Depends(require_role("staff")),
    connection: Any = Depends(get_connection),
) -> MemberProfile:
    return MemberProfile(**await _require_member(connection, member_id))


@router.get("/{member_id}/loans", response_model=PaginatedLoanHistory)
async def get_member_loans(
    member_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(require_role("staff")),
    connection: Any = Depends(get_connection),
) -> PaginatedLoanHistory:
    await _require_member(connection, member_id)
    items = [
        LoanHistoryEntry(**loan)
        for loan in await list_loans_for_member(connection, member_id, limit, offset)
    ]
    total = await count_loans_for_member(connection, member_id)
    return PaginatedLoanHistory(items=items, total=total, limit=limit, offset=offset)


@router.get("/{member_id}/reservations", response_model=PaginatedReservations)
async def get_member_reservations(
    member_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(require_role("staff")),
    connection: Any = Depends(get_connection),
) -> PaginatedReservations:
    await _require_member(connection, member_id)
    items = [
        ReservationHistoryEntry(**reservation)
        for reservation in await list_reservations_for_member(
            connection, member_id, limit, offset
        )
    ]
    total = await count_reservations_for_member(connection, member_id)
    return PaginatedReservations(items=items, total=total, limit=limit, offset=offset)


@router.get("/{member_id}/fines", response_model=PaginatedFines)
async def get_member_fines(
    member_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _principal: Principal = Depends(require_role("staff")),
    connection: Any = Depends(get_connection),
) -> PaginatedFines:
    await _require_member(connection, member_id)
    items = [
        FineHistoryEntry(**fine)
        for fine in await list_fines_for_member(connection, member_id, limit, offset)
    ]
    total = await count_fines_for_member(connection, member_id)
    return PaginatedFines(items=items, total=total, limit=limit, offset=offset)
