import logging

from fastapi import APIRouter
from core.database import get_pool
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        logger.exception("[health] database unreachable")
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
        )
