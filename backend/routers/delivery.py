from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from core.database import get_db
from models.delivery import DeliveryValidateRequest, DeliveryValidateResponse
import services.delivery_service as delivery_service

router = APIRouter(prefix="/api")


@router.post("/delivery/validate", response_model=DeliveryValidateResponse)
async def validate_delivery_zip(request: DeliveryValidateRequest, db=Depends(get_db)):
    try:
        result = await delivery_service.validate_zip(db, request.zip_code)
        if result:
            return DeliveryValidateResponse(is_covered=True, city=result["city"])
        return DeliveryValidateResponse(is_covered=False, city=None)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "message": "Service temporarily unavailable",
            },
        )
