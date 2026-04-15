from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import get_db
from services.notification_service import send_reservation_reminders
from services.monitor_service import (
    collect_snapshot,
    check_thresholds,
    run_monitor,
)

router = APIRouter(prefix="/api/internal")


@router.post("/send-reminders")
async def send_reminders(
    x_internal_token: str | None = Header(default=None),
    db=Depends(get_db),
):
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    sent = await send_reservation_reminders(db)
    return JSONResponse(status_code=200, content={"sent": sent})


@router.get("/monitor")
async def trigger_monitor(
    x_internal_token: str | None = Header(default=None),
    db=Depends(get_db),
):
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    from datetime import datetime, timezone

    snapshot = await collect_snapshot(db, settings.monitor_window_hours)
    breaching = check_thresholds(snapshot)
    await run_monitor(breaching, snapshot)

    thresholds = {
        "error_rate": settings.monitor_error_rate_threshold,
        "p95_latency_ms": settings.monitor_latency_p95_threshold_ms,
        "notification_failures": settings.monitor_notification_failure_threshold,
    }
    metrics = {
        name: {
            **snapshot[name],
            "threshold": thresholds[name],
            "breaching": name in breaching,
        }
        for name in snapshot
    }
    return JSONResponse(
        status_code=200,
        content={
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "window_hours": settings.monitor_window_hours,
            "metrics": metrics,
            "alerts_fired": bool(breaching),
        },
    )
