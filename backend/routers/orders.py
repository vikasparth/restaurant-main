from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from core.database import get_db
from core.errors import error_response
from models.order import OrderCreateRequest
from services.config_service import get_restaurant_config
from services.order_service import create_order

router = APIRouter(prefix="/api")


@router.post("/orders")
async def  order_create(request: OrderCreateRequest, db=Depends(get_db)):
    try:
        config = await  get_restaurant_config(db)
        result = await create_order(db, request, config)
        return result   
    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"code": "DB_UNAVAILABLE", "error": "Service temporarily unavailable"},
        )

        