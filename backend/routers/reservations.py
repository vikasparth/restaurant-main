from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from core.database import get_db
from models.reservation import ReservationCreateRequest
from services.config_service import get_restaurant_config
from services.reservation_service import create_reservation
from core.rate_limit import limiter

router = APIRouter(prefix="/api")


@router.post("/reservations")
@limiter.limit("20/minute")
async def reservation_create(
    request: Request, body: ReservationCreateRequest, db=Depends(get_db)
):
    try:
        config = await get_restaurant_config(db)
        result = await create_reservation(db, body, config)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[reservations] unexpected error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "error": "Service temporarily unavailable",
            },
        )
