from fastapi import APIRouter
from core.database import get_pool
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
        )
