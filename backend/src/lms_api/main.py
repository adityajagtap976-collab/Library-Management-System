from fastapi import FastAPI

from lms_api.routers.auth import router as auth_router
from lms_api.routers.me import router as me_router

app = FastAPI(title="Library Management System API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(me_router, tags=["me"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
