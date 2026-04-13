from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from core.database import get_db
from models.order import OrderCreateRequest
from services.config_service import get_restaurant_config
from services.order_service import create_order
from core.rate_limit import limiter

router = APIRouter(prefix="/api")


@router.post("/orders")
@limiter.limit("20/minute")
async def order_create(request: Request, body: OrderCreateRequest, db=Depends(get_db)):
    try:
        config = await get_restaurant_config(db)
        result = await create_order(db, body, config)
        return result
    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "error": "Service temporarily unavailable",
            },
        )
