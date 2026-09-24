import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lms_api.db.session import close_pool, open_pool
from lms_api.routers.auth import router as auth_router
from lms_api.routers.catalog import router as catalog_router
from lms_api.routers.fines import router as fines_router
from lms_api.routers.loans import router as loans_router
from lms_api.routers.me import router as me_router
from lms_api.routers.members import router as members_router
from lms_api.routers.reservations import router as reservations_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Open the pool at startup, not on the first request. If ORACLE_DSN,
    # ORACLE_USER, or ORACLE_PASSWORD are wrong, this makes the container
    # crash-loop on deploy with a clear error in the platform's logs,
    # instead of silently accepting traffic and failing on someone's
    # first real request.
    await open_pool()
    yield
    await close_pool()


app = FastAPI(title="Library Management System API", lifespan=lifespan)

# CORS_ORIGINS is a comma-separated list, e.g.:
#   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
# Unset -> "*" so local development and early Swagger-only testing isn't
# blocked. Set this explicitly once the frontend has a real deployed URL --
# an API that only ever receives JWT-bearer requests (no cookies) is lower
# risk with open CORS than a cookie-auth API would be, but "lower risk"
# is not the same as "fine to ship" once you have a real frontend origin
# to pin it to.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_origins == "*" else _cors_origins.split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(catalog_router, tags=["catalog"])
app.include_router(loans_router, tags=["loans"])
app.include_router(me_router, tags=["me"])
app.include_router(members_router, tags=["members"])
app.include_router(reservations_router, tags=["reservations"])
app.include_router(fines_router, tags=["fines"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}