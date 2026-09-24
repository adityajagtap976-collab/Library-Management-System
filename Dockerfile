FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy lockfile + pyproject first so dependency install is cached
# separately from application code changes.
COPY pyproject.toml uv.lock ./
COPY backend/src ./backend/src
COPY README.md ./README.md

# --locked: fail the build if uv.lock is out of date, instead of
# silently resolving different versions than what's tested in CI.
# --no-dev: pytest/mypy/ruff have no business in a production image.
RUN uv sync --locked --no-dev

# Most hosts (Render, Railway) inject $PORT at runtime; 8000 is the
# local-run fallback so `docker run -p 8000:8000 ...` works untouched.
ENV PORT=8000
EXPOSE 8000

# Required at runtime, not build time: ORACLE_USER, ORACLE_PASSWORD,
# ORACLE_DSN, JWT_SECRET_KEY, and optionally CORS_ORIGINS.
CMD ["sh", "-c", "uv run uvicorn lms_api.main:app --host 0.0.0.0 --port ${PORT} --app-dir backend/src"]
