from fastapi import APIRouter, Depends

from lms_api.core.dependencies import Principal, require_role

router = APIRouter()


@router.get("/members/me")
async def member_me(
    principal: Principal = Depends(require_role("member")),
) -> dict[str, str]:
    return {
        "member_id": str(principal["sub"]),
        "email": str(principal["email"]),
    }


@router.get("/staff/me")
async def staff_me(
    principal: Principal = Depends(require_role("staff")),
) -> dict[str, str]:
    return {
        "staff_id": str(principal["sub"]),
        "email": str(principal["email"]),
    }
