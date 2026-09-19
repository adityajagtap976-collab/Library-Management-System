from fastapi import FastAPI

from lms_api.routers.auth import router as auth_router

app = FastAPI(title="Library Management System API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
