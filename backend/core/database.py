import asyncpg

from core.config import settings

# Pool is initialised on startup and closed on shutdown
_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=str(settings.database_url),
        min_size=2,
        max_size=10,
    )


async def disconnect() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised")
    return _pool


async def get_db():
    """FastAPI dependency — provides a single DB connection per request."""
    async with _pool.acquire() as connection:
        yield connection
