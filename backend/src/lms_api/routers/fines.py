from typing import cast

import oracledb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from lms_api.core.dependencies import Principal, require_role
from lms_api.db.session import get_connection
from lms_api.models.fines import (
    FineGenerated,
    FineHistoryEntry,
    FinePaid,
    PaginatedFines,
)
from lms_api.repositories.fines import (
    count_fines_for_member,
    generate_overdue_fines,
    list_fines_for_member,
    mark_fine_paid,
)

router = APIRouter(prefix="/fines")


@router.post("/generate-overdue", response_model=FineGenerated)
async def generate_overdue_fines_endpoint(
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> FineGenerated:
    return FineGenerated(fines_created=await generate_overdue_fines(connection))


@router.get("/mine", response_model=PaginatedFines)
async def list_my_fines(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role("member")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> PaginatedFines:
    member_id = int(cast(str, principal["sub"]))
    items = [
        FineHistoryEntry(**fine)
        for fine in await list_fines_for_member(connection, member_id, limit, offset)
    ]
    total = await count_fines_for_member(connection, member_id)
    return PaginatedFines(items=items, total=total, limit=limit, offset=offset)


@router.patch("/{fine_id}/pay", response_model=FinePaid)
async def pay_fine(
    fine_id: int,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> FinePaid:
    result = await mark_fine_paid(connection, fine_id)
    if result["outcome"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found"
        )
    if result["outcome"] == "already_paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Fine was already paid on {result['paid_date']}",
        )
    return FinePaid(fine_id=fine_id, paid_date=result["paid_date"])
