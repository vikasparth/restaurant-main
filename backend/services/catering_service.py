import logging
from datetime import date, datetime, timedelta

from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import error_response
from core.timezone import now_in_restaurant_time
from services.delivery_service import validate_zip
from services.reference_service import generate_reference_number
from services.notification_service import notify_catering

logger = logging.getLogger(__name__)


async def fetch_catering_items(db, items: list) -> list[dict]:
    """Fetch DB rows for each requested item. Validates availability and catering eligibility.

    Returns list of dicts with item_id, name, price_per_tray, trays.
    Raises 422 JSONResponse on any invalid item.
    """
    item_ids = [i.item_id for i in items]
    trays_map = {i.item_id: i.trays for i in items}

    rows = await db.fetch(
        """
        SELECT id, name, is_available, catering_available, catering_price_per_tray
        FROM   menu_items
        WHERE  id = ANY($1::text[]) AND location_id = $2
        """,
        item_ids,
        settings.location_id,
    )

    found_ids = {r["id"] for r in rows}
    for item_id in item_ids:
        if item_id not in found_ids:
            raise _validation_error(
                "Menu item not found or unavailable", "INVALID_MENU_ITEM"
            )

    for row in rows:
        if not row["is_available"]:
            raise _validation_error(
                "Menu item not found or unavailable", "INVALID_MENU_ITEM"
            )
        if not row["catering_available"]:
            raise _validation_error(
                f"Item '{row['id']}' is not available for catering",
                "ITEM_NOT_CATERING_AVAILABLE",
            )

    return [
        {
            "item_id": row["id"],
            "name": row["name"],
            "price_per_tray": float(row["catering_price_per_tray"]),
            "trays": trays_map[row["id"]],
        }
        for row in rows
    ]


def _validation_error(message: str, code: str) -> Exception:
    """Wrap a JSONResponse in an exception so it can be raised from a helper."""
    response = error_response(message, code, 422)
    exc = Exception(code)
    exc.response = response  # type: ignore[attr-defined]
    return exc


async def create_catering_order(db, payload, config: dict) -> JSONResponse:
    """Validate and save a catering order. Returns 201 on success, 200 on duplicate."""
    # --- Idempotency check ---
    existing = await db.fetchrow(
        """
        SELECT reference_number, status, total::float, event_date::text, event_time
        FROM   catering_orders
        WHERE  idempotency_key = $1
        """,
        payload.idempotency_key,
    )
    if existing:
        row = dict(existing)
        deposit_amount = round(
            row["total"] * config["catering_deposit_percent"] / 100, 2
        )
        return JSONResponse(
            status_code=200,
            content={
                "reference_number": row["reference_number"],
                "status": row["status"],
                "total_amount": row["total"],
                "deposit_amount": deposit_amount,
                "event_date": row["event_date"],
                "event_time": row["event_time"],
            },
        )

    # --- 48-hour advance rule ---
    tz = config["timezone"]
    now = now_in_restaurant_time(tz)
    event_dt = datetime.strptime(
        f"{payload.event_date} {payload.event_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=now.tzinfo)
    advance_hours = config["catering_advance_hours"]
    if event_dt < now + timedelta(hours=advance_hours):
        return error_response(
            f"Catering orders must be placed at least {advance_hours} hours in advance",
            "LESS_THAN_48_HOURS",
            422,
        )

    # --- Zip code validation ---
    zone = await validate_zip(db, payload.zip_code)
    if zone is None:
        return error_response(
            "Zip code is not in our delivery area", "ZIP_NOT_COVERED", 422
        )

    # --- Validate items and fetch DB prices ---
    try:
        line_items = await fetch_catering_items(db, payload.items)
    except Exception as exc:
        if hasattr(exc, "response"):
            return exc.response  # type: ignore[attr-defined]
        raise

    # --- Minimum order check ---
    total = round(sum(item["price_per_tray"] * item["trays"] for item in line_items), 2)
    min_order = float(config["min_catering_order"])
    if total < min_order:
        return error_response(
            f"Minimum catering order is ${min_order:.2f}",
            "BELOW_MIN_CATERING_ORDER",
            422,
        )

    deposit_amount = round(total * config["catering_deposit_percent"] / 100, 2)
    reference_number = await generate_reference_number(db)
    event_date_obj = date.fromisoformat(payload.event_date)

    # --- Save order ---
    order_id = await db.fetchval(
        """
        INSERT INTO catering_orders
          (location_id, idempotency_key, reference_number, customer_name,
           customer_email, customer_phone, event_date, event_time,
           delivery_address, delivery_zip, total, special_instructions)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
        """,
        settings.location_id,
        payload.idempotency_key,
        reference_number,
        payload.customer_name,
        payload.customer_email,
        payload.customer_phone,
        event_date_obj,
        payload.event_time,
        payload.delivery_address,
        payload.zip_code,
        total,
        payload.special_instructions,
    )

    # --- Save line items (price snapshot) ---
    for item in line_items:
        await db.execute(
            """
            INSERT INTO catering_order_items
              (catering_order_id, menu_item_id, name, price_per_tray, trays)
            VALUES ($1, $2, $3, $4, $5)
            """,
            order_id,
            item["item_id"],
            item["name"],
            item["price_per_tray"],
            item["trays"],
        )

    # --- Fire notifications (failures are logged, never block the response) ---
    logger.info(
        "[catering] catering order created — reference: %s",
        reference_number,
        extra={"event": "catering_order_created", "reference": reference_number},
    )
    await notify_catering(
        {
            "reference_number": reference_number,
            "customer_name": payload.customer_name,
            "customer_email": payload.customer_email,
            "customer_phone": payload.customer_phone,
            "event_date": payload.event_date,
            "event_time": payload.event_time,
            "delivery_address": payload.delivery_address,
            "total_amount": total,
            "deposit_amount": deposit_amount,
            "line_items": line_items,
            "special_instructions": payload.special_instructions,
        }
    )

    return JSONResponse(
        status_code=201,
        content={
            "reference_number": reference_number,
            "status": "confirmed",
            "total_amount": total,
            "deposit_amount": deposit_amount,
            "event_date": payload.event_date,
            "event_time": payload.event_time,
        },
    )
