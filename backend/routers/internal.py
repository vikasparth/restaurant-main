import os

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from core.database import get_db
from services.notification_service import send_reservation_reminders

router = APIRouter(prefix="/api/internal")

INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "test-secret")

@router.post("/send-reminders")
async def send_reminders(
    x_internal_token: str | None = Header(default=None),
    db=Depends(get_db),
):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    sent = await send_reservation_reminders(db)
    return JSONResponse(status_code=200, content={"sent": sent})
