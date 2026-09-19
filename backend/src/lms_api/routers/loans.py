from typing import cast

import oracledb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from lms_api.core.dependencies import Principal, require_role
from lms_api.db.session import get_connection
from lms_api.models.loans import (
    LoanCreate,
    LoanCreated,
    LoanHistoryEntry,
    LoanReturned,
    PaginatedLoanHistory,
)
from lms_api.repositories.loans import (
    count_loans_for_member,
    create_loan,
    list_loans_for_member,
    mark_loan_returned,
)

router = APIRouter(prefix="/loans")


@router.get("/mine", response_model=PaginatedLoanHistory)
async def list_my_loans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role("member")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> PaginatedLoanHistory:
    member_id = int(cast(str, principal["sub"]))
    items = [
        LoanHistoryEntry(**loan)
        for loan in await list_loans_for_member(connection, member_id, limit, offset)
    ]
    total = await count_loans_for_member(connection, member_id)
    return PaginatedLoanHistory(items=items, total=total, limit=limit, offset=offset)


def _database_error_details(error: oracledb.DatabaseError) -> tuple[int | None, str]:
    database_error = error.args[0] if error.args else None
    code = getattr(database_error, "code", None)
    message = getattr(database_error, "message", "")
    return (int(code) if code is not None else None, str(message))


@router.post("", response_model=LoanCreated, status_code=status.HTTP_201_CREATED)
async def create_loan_endpoint(
    loan: LoanCreate,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> LoanCreated:
    try:
        created_loan = await create_loan(connection, loan.member_id, loan.copy_id)
    except oracledb.DatabaseError as error:
        code, message = _database_error_details(error)
        if code == 20004:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Copy is not available for loan",
            ) from error
        if code == 20005:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Member is not active and cannot check out books",
            ) from error
        if code == 2291 and "FK_LOANS_COPY" in message.upper():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Copy not found",
            ) from error
        if code == 2291 and "FK_LOANS_MEMBER" in message.upper():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            ) from error
        raise
    return LoanCreated(**created_loan)


@router.patch("/{loan_id}/return", response_model=LoanReturned)
async def return_loan(
    loan_id: int,
    _principal: Principal = Depends(require_role("staff")),
    connection: oracledb.AsyncConnection = Depends(get_connection),
) -> LoanReturned:
    try:
        result = await mark_loan_returned(connection, loan_id)
    except oracledb.DatabaseError:  # noqa: TRY203
        raise

    if result["outcome"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    if result["outcome"] == "already_returned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Loan was already returned on {result['return_date']}",
        )
    return LoanReturned(loan_id=loan_id, **result)
