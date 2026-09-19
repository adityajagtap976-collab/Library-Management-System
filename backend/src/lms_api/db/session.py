import os
from collections.abc import AsyncIterator

import oracledb

_pool: oracledb.AsyncConnectionPool | None = None


async def open_pool() -> oracledb.AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool_async(
            user=os.environ["ORACLE_USER"],
            password=os.environ["ORACLE_PASSWORD"],
            dsn=os.environ["ORACLE_DSN"],
            min=1,
            max=5,
            increment=1,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_connection() -> AsyncIterator[oracledb.AsyncConnection]:
    pool = await open_pool()
    async with pool.acquire() as connection:
        yield connection
