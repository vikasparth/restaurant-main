from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from core.database import get_db
from models.catering import CateringCreateRequest
from services.catering_service import create_catering_order
from services.config_service import get_restaurant_config
from core.rate_limit import limiter

router = APIRouter(prefix="/api")


@router.post("/catering")
@limiter.limit("20/minute")
async def catering_create(
    request: Request, body: CateringCreateRequest, db=Depends(get_db)
):
    try:
        config = await get_restaurant_config(db)
        return await create_catering_order(db, body, config)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "error": "Service temporarily unavailable",
            },
        )
