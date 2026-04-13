from datetime import datetime, date
from zoneinfo import ZoneInfo

from fastapi import status
from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import error_response
from core.timezone import now_in_restaurant_time
from services.config_service import get_restaurant_config
from services.notification_service import notify_order
from services.delivery_service import validate_zip
from services.menu_service import validate_menu_items
from services.reference_service import generate_reference_number

def validate_scheduled_time(
    scheduled_date: str,
    scheduled_time: str,
    config: dict,
) -> JSONResponse | None:
    tz = config["timezone"]
    now = now_in_restaurant_time(tz)

    # Combine date + time into a single datetime in the restaurant's timezone
    dt = datetime.strptime(
        f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M"
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

    return None   # None means all checks passed

async def calculate_totals(
    db,
    items: list,
    order_type: str,
    config: dict,
) -> tuple:
    # Fetch current prices for all requested item IDs in one query
    item_ids = [item.menu_item_id for item in items]
    rows = await db.fetch(
        """
        SELECT id, name, price
        FROM   menu_items
        WHERE  id = ANY($1::text[])
          AND  location_id = $2
        """,
        item_ids,
        settings.location_id,
    )
    price_map = {row["id"]: row for row in rows}

    # Build line items with snapshotted prices
    line_items = []
    subtotal = 0.0
    for item in items:
        row = price_map[item.menu_item_id]
        line_total = float(row["price"]) * item.quantity
        subtotal += line_total
        line_items.append({
            "menu_item_id": item.menu_item_id,
            "name":         row["name"],
            "price":        float(row["price"]),
            "quantity":     item.quantity,
        })

    subtotal      = round(subtotal, 2)
    delivery_fee  = float(config["delivery_fee"]) if order_type == "delivery" else 0.0
    total         = round(subtotal + delivery_fee, 2)

    return line_items, subtotal, delivery_fee, total

async def create_order(db, payload, config: dict) -> JSONResponse:
    # Step 1 — check idempotency: has this request been submitted before?
    existing = await db.fetchrow(
        """
        SELECT reference_number, status, order_type,
               scheduled_date::text, scheduled_time,
               subtotal, delivery_fee, total
        FROM   orders
        WHERE  idempotency_key = $1
        """,
        payload.idempotency_key,
    )
    if existing:
        row = dict(existing)
        return JSONResponse(status_code=200, content={
            "reference_number": row["reference_number"],
            "status":           row["status"],
            "order_type":       row["order_type"],
            "scheduled_date":   row["scheduled_date"],
            "scheduled_time":   row["scheduled_time"],
            "subtotal":         float(row["subtotal"]),
            "delivery_fee":     float(row["delivery_fee"]),
            "total":            float(row["total"]),
        })

    # Step 2 — validate scheduled time (past check + hours check)
    err = validate_scheduled_time(payload.scheduled_date, payload.scheduled_time, config)
    if err:
        return err

    # Step 3 — validate all menu items exist and are available
    item_ids = [item.menu_item_id for item in payload.items]
    await validate_menu_items(db, item_ids)

    # Step 4 — for delivery orders: validate zip and minimum order
    if payload.order_type == "delivery":
        zone = await validate_zip(db, payload.delivery_zip)
        if not zone:
            return error_response("Zip code is not in our delivery area", "ZIP_NOT_COVERED", 422)

    # Step 5 — calculate prices (snapshot from DB)
    line_items, subtotal, delivery_fee, total = await calculate_totals(
        db, payload.items, payload.order_type, config
    )

    # Step 6 — enforce minimum delivery order value
    if payload.order_type == "delivery":
        min_order = float(config["min_delivery_order"])
        if subtotal < min_order:
            return error_response(
                f"Minimum delivery order is ${min_order:.2f}", "BELOW_MIN_ORDER", 422
            )

    # Step 7 — generate reference number and save order to DB
    scheduled_date_obj = date.fromisoformat(payload.scheduled_date)
    reference_number = await generate_reference_number(db)

    order_id = await db.fetchval(
        """
        INSERT INTO orders (
            location_id, idempotency_key, reference_number,
            customer_name, customer_email, customer_phone,
            order_type, status, scheduled_date, scheduled_time,
            delivery_address, delivery_zip,
            subtotal, delivery_fee, total, special_instructions
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,'confirmed',$8,$9,$10,$11,$12,$13,$14,$15)
        RETURNING id
        """,
        settings.location_id,
        payload.idempotency_key,
        reference_number,
        payload.customer_name,
        payload.customer_email,
        payload.customer_phone,
        payload.order_type,
        scheduled_date_obj,
        payload.scheduled_time,
        payload.delivery_address,
        payload.delivery_zip,
        subtotal,
        delivery_fee,
        total,
        payload.special_instructions,
    )

    # Step 8 — save order line items (snapshotted prices)
    for item in line_items:
        await db.execute(
            """
            INSERT INTO order_items (order_id, menu_item_id, name, price, quantity)
            VALUES ($1, $2, $3, $4, $5)
            """,
            order_id,
            item["menu_item_id"],
            item["name"],
            item["price"],
            item["quantity"],
        )

    # Step 9 — fire notifications (failures are logged, never block the response)
    await notify_order({
        "reference_number":   reference_number,
        "customer_name":      payload.customer_name,
        "customer_email":     payload.customer_email,
        "customer_phone":     payload.customer_phone,
        "order_type":         payload.order_type,
        "scheduled_time":     f"{payload.scheduled_date} {payload.scheduled_time}",
        "total_amount":       total,
        "delivery_fee":       delivery_fee,
        "line_items":         line_items,
        "special_instructions": payload.special_instructions,
    })

    # Step 10 — return the response
    return JSONResponse(status_code=201, content={
        "reference_number": reference_number,
        "status":           "confirmed",
        "order_type":       payload.order_type,
        "scheduled_date":   payload.scheduled_date,
        "scheduled_time":   payload.scheduled_time,
        "subtotal":         subtotal,
        "delivery_fee":     delivery_fee,
        "total":            total,
    })
