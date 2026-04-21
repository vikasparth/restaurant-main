from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from core.database import get_db
from models.menu import MenuResponse
import services.menu_service as menu_service

router = APIRouter(prefix="/api")


@router.get("/menu", response_model=MenuResponse)
async def get_menu(db=Depends(get_db)):
    try:
        rows = await menu_service.get_menu_items(db)
        return menu_service.group_by_category(rows)
    except Exception as e:
        print(f"[menu] unexpected error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_UNAVAILABLE",
                "message": "Service temporarily unavailable",
            },
        )
