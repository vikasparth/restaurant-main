import asyncio
import logging
import time
from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

# Holds the correlation ID for the current request.
# ContextVar is safe in async code — each request gets its own isolated value.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger("aap_ki_rasoi")


async def _log_to_db(
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    request_id: str,
) -> None:
    try:
        from core.database import get_pool

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO request_logs
                    (method, path, status_code, duration_ms, request_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                method,
                path,
                status_code,
                duration_ms,
                request_id,
            )
    except Exception:
        logger.exception("Failed to write request log — continuing")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid4())
        request_id_var.set(request_id)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)
        asyncio.create_task(
            _log_to_db(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
            )
        )

        return response
