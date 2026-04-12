from datetime import datetime, date
from zoneinfo import ZoneInfo

from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import error_response
from core.timezone import now_in_restaurant_time
from services.config_service import get_restaurant_config
from services.reference_service import generate_reference_number

def validate_reservation_time(
        reserved_date: str,
        reserved_time: str,
        config: dict
        ) -> JSONResponse | None:
    
    tz = config["timezone"]
    now = now_in_restaurant_time(tz)

    # Combine date + time into a single datetime in the restaurant's timezone
    dt = datetime.strptime(
        f"{reserved_date} {reserved_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=ZoneInfo(tz))

    # Check 1 — must be in the future
    if dt <= now:
        return error_response("Scheduled time is in the past", "SCHEDULED_TIME_IN_PAST", 422)
    
    # Check 2 — restaurant must not be closed that day
    day_name = dt.strftime("%A").lower()   # e.g. "wednesday"
    if day_name in config["closed_days"]:
        return error_response("Restaurant is closed on that day", "RESTAURANT_CLOSED", 422)

    # Check 3 — time must be within operating hours for that day
    hours = config["operating_hours"].get(day_name)
    if not hours:
        return error_response("Restaurant is closed on that day", "RESTAURANT_CLOSED", 422)
    
    open_time  = datetime.strptime(hours["open"],  "%H:%M").time()
    close_time = datetime.strptime(hours["close"], "%H:%M").time()
    order_time = dt.time()

    if not (open_time <= order_time <= close_time):
        return error_response("Scheduled time is outside operating hours", "OUTSIDE_HOURS", 422)

    return None
