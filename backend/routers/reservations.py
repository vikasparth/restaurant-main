from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from core.database import get_db
from models.reservation import ReservationCreateRequest
from services.config_service import get_restaurant_config
from services.reservation_service import create_reservation

router = APIRouter(prefix="/api")


@router.post("/reservations")
async def reservation_create(request: ReservationCreateRequest, db=Depends(get_db)):
    try:
        config = await get_restaurant_config(db)
        result = await create_reservation(db, request, config)
        return result
    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"code": "DB_UNAVAILABLE", "error": "Service temporarily unavailable"},
        )
