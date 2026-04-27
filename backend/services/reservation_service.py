import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo

from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import error_response
from core.timezone import now_in_restaurant_time
from services.notification_service import notify_reservation
from services.reference_service import generate_reference_number

logger = logging.getLogger(__name__)


def validate_reservation_time(
    reserved_date: str, reserved_time: str, config: dict
) -> JSONResponse | None:

    tz = config["timezone"]
    now = now_in_restaurant_time(tz)

    # Combine date + time into a single datetime in the restaurant's timezone
    dt = datetime.strptime(
        f"{reserved_date} {reserved_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=ZoneInfo(tz))

    # Check 1 — must be in the future
    if dt <= now:
        return error_response(
            "Scheduled time is in the past", "SCHEDULED_TIME_IN_PAST", 422
        )

    # Check 2 — restaurant must not be closed that day
    day_name = dt.strftime("%A").lower()  # e.g. "wednesday"
    if day_name in config["closed_days"]:
        return error_response(
            "Restaurant is closed on that day", "RESTAURANT_CLOSED", 422
        )

    # Check 3 — time must be within operating hours for that day
    hours = config["operating_hours"].get(day_name)
    if not hours:
        return error_response(
            "Restaurant is closed on that day", "RESTAURANT_CLOSED", 422
        )

    open_time = datetime.strptime(hours["open"], "%H:%M").time()
    close_time = datetime.strptime(hours["close"], "%H:%M").time()
    order_time = dt.time()

    if not (open_time <= order_time <= close_time):
        return error_response(
            "Scheduled time is outside operating hours", "OUTSIDE_HOURS", 422
        )

    return None


async def create_reservation(db, payload, config: dict) -> JSONResponse:
    # Step 1 — idempotency check
    existing = await db.fetchrow(
        """
        SELECT reference_number, status, party_size,
               reserved_date::text, reserved_time
        FROM   reservations
        WHERE  idempotency_key = $1
        """,
        payload.idempotency_key,
    )
    if existing:
        row = dict(existing)
        return JSONResponse(
            status_code=200,
            content={
                "reference_number": row["reference_number"],
                "status": row["status"],
                "party_size": row["party_size"],
                "reserved_date": row["reserved_date"],
                "reserved_time": row["reserved_time"],
            },
        )

    # Step 2 — validate time (past check + hours check)
    err = validate_reservation_time(
        payload.reserved_date, payload.reserved_time, config
    )
    if err:
        return err

    # Step 3 — party size check
    max_party = config["max_reservation_party_size"]
    if payload.party_size > max_party:
        return error_response(
            f"Party size exceeds maximum of {max_party}", "PARTY_SIZE_EXCEEDED", 422
        )

    # Step 4 — generate reference number and save to DB
    reserved_date_obj = date.fromisoformat(payload.reserved_date)
    reference_number = await generate_reference_number(db)

    await db.execute(
        """
        INSERT INTO reservations (
            location_id, idempotency_key, reference_number,
            customer_name, customer_email, customer_phone,
            party_size, reserved_date, reserved_time,
            notes, status
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'confirmed')
        """,
        settings.location_id,
        payload.idempotency_key,
        reference_number,
        payload.customer_name,
        payload.customer_email,
        payload.customer_phone,
        payload.party_size,
        reserved_date_obj,
        payload.reserved_time,
        payload.notes,
    )

    # Step 5 — fire notifications (failures are logged, never block the response)
    logger.info(
        "[reservations] reservation confirmed — reference: %s", reference_number,
        extra={"event": "reservation_confirmed", "reference": reference_number},
    )
    await notify_reservation(
        {
            "reference_number": reference_number,
            "customer_name": payload.customer_name,
            "customer_email": payload.customer_email,
            "customer_phone": payload.customer_phone,
            "reservation_date": payload.reserved_date,
            "reservation_time": payload.reserved_time,
            "party_size": payload.party_size,
            "special_instructions": payload.notes,
        }
    )

    # Step 6 — return the response
    return JSONResponse(
        status_code=201,
        content={
            "reference_number": reference_number,
            "status": "confirmed",
            "party_size": payload.party_size,
            "reserved_date": payload.reserved_date,
            "reserved_time": payload.reserved_time,
        },
    )
