from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from core.database import get_db
from models.catering import CateringCreateRequest
from services.catering_service import create_catering_order
from services.config_service import get_restaurant_config

router = APIRouter(prefix="/api")


@router.post("/catering")
async def catering_create(request: CateringCreateRequest, db=Depends(get_db)):
    try:
        config = await get_restaurant_config(db)
        return await create_catering_order(db, request, config)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "error": "Service temporarily unavailable",
            },
        )
