from fastapi import FastAPI

from lms_api.routers.auth import router as auth_router
from lms_api.routers.catalog import router as catalog_router
from lms_api.routers.fines import router as fines_router
from lms_api.routers.loans import router as loans_router
from lms_api.routers.me import router as me_router
from lms_api.routers.reservations import router as reservations_router

app = FastAPI(title="Library Management System API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(catalog_router, tags=["catalog"])
app.include_router(loans_router, tags=["loans"])
app.include_router(me_router, tags=["me"])
app.include_router(reservations_router, tags=["reservations"])
app.include_router(fines_router, tags=["fines"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
