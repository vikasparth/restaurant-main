# Tests for Slice 3 — Orders
# Spec: specs/slice3_orders.md
# TDD: all tests written first — they will all FAIL until the orders endpoint is built.
#
# Run with: pytest tests/test_orders.py -v

import re
import uuid
from datetime import date, timedelta

import pytest

from core.database import get_pool

# ---------------------------------------------------------------------------
# Seed data reference (from 20260406000002_seed_data.sql)
#   samosa          $5.99   available
#   chicken-tikka   $14.99  available
#   butter-chicken  $16.99  available
#   dal-makhani     $13.99  available
#   garlic-naan     $3.99   available
#   mango-lassi     $4.99   available
#   delivery_fee    $4.99
#   min_delivery    $25.00
#   operating hours Wed: 11:00–21:00
# ---------------------------------------------------------------------------

_future = date.today() + timedelta(days=60)  # always well in the future
VALID_DATE = _future.strftime("%Y-%m-%d")
VALID_TIME = "18:00"  # Within 11:00–21:00 window
VALID_ZIP = "98004"  # Active delivery zone (Bellevue)


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def pickup_payload(**overrides) -> dict:
    """Minimal valid pickup order. samosa×2 + butter-chicken×1 = $28.97."""
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Priya Sharma",
        "customer_email": "priya@example.com",
        "customer_phone": "4255550123",
        "order_type": "pickup",
        "scheduled_date": VALID_DATE,
        "scheduled_time": VALID_TIME,
        "items": [
            {"menu_item_id": "butter-chicken", "quantity": 1},  # $16.99
            {"menu_item_id": "samosa", "quantity": 2},  # $11.98
        ],
    }
    base.update(overrides)
    return base


def delivery_payload(**overrides) -> dict:
    """Minimal valid delivery order. butter-chicken×2 = $33.98 (above $25 min)."""
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Priya Sharma",
        "customer_email": "priya@example.com",
        "customer_phone": "4255550123",
        "order_type": "delivery",
        "scheduled_date": VALID_DATE,
        "scheduled_time": VALID_TIME,
        "items": [
            {"menu_item_id": "butter-chicken", "quantity": 2},  # $33.98
        ],
        "delivery_address": "123 Main St",
        "delivery_zip": VALID_ZIP,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# ORD-01  Valid pickup order — 201 + reference number + status
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_valid_pickup_order_returns_201(client):
    response = await client.post("/api/orders", json=pickup_payload())
    assert response.status_code == 201
    body = response.json()
    assert "reference_number" in body
    assert body["status"] == "confirmed"
    assert body["order_type"] == "pickup"


# ---------------------------------------------------------------------------
# ORD-02  Valid delivery order — 201 + delivery fee applied
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_valid_delivery_order_returns_201(client):
    response = await client.post("/api/orders", json=delivery_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["order_type"] == "delivery"
    assert body["delivery_fee"] == 4.99
    assert body["total"] == round(body["subtotal"] + 4.99, 2)


# ---------------------------------------------------------------------------
# ORD-03  Pickup order has zero delivery fee
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_pickup_order_has_zero_delivery_fee(client):
    response = await client.post("/api/orders", json=pickup_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["delivery_fee"] == 0
    assert body["total"] == body["subtotal"]


# ---------------------------------------------------------------------------
# ORD-04  Price snapshot — order_items.price matches menu_items.price at order time
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_price_snapshot_on_order_items(client):
    # butter-chicken×1 ($16.99) + samosa×2 ($5.99 each = $11.98) = $28.97
    expected_subtotal = round(16.99 + 5.99 * 2, 2)

    response = await client.post("/api/orders", json=pickup_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["subtotal"] == expected_subtotal

    # Verify the prices are snapshotted in order_items in the DB
    ref = body["reference_number"]
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT oi.menu_item_id, oi.price, oi.quantity
            FROM   order_items oi
            JOIN   orders      o  ON o.id = oi.order_id
            WHERE  o.reference_number = $1
            ORDER  BY oi.menu_item_id
            """,
            ref,
        )
    assert len(rows) == 2
    prices = {r["menu_item_id"]: float(r["price"]) for r in rows}
    assert prices["butter-chicken"] == 16.99
    assert prices["samosa"] == 5.99


# ---------------------------------------------------------------------------
# ORD-05  Reference number format — AKR-YYYYMMDD-XXXX
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_reference_number_format(client):
    response = await client.post("/api/orders", json=pickup_payload())
    assert response.status_code == 201
    ref = response.json()["reference_number"]
    assert re.fullmatch(r"AKR-\d{8}-\d{4}", ref), f"Unexpected format: {ref}"


# ---------------------------------------------------------------------------
# ORD-06  Scheduled time outside operating hours → 422 OUTSIDE_HOURS
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_scheduled_time_outside_hours_returns_422(client):
    # Wednesday closes at 21:00 — 23:00 is outside
    response = await client.post(
        "/api/orders",
        json=pickup_payload(scheduled_time="23:00"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "OUTSIDE_HOURS"


# ---------------------------------------------------------------------------
# ORD-07  Scheduled time in the past → 422 SCHEDULED_TIME_IN_PAST
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_scheduled_time_in_past_returns_422(client):
    response = await client.post(
        "/api/orders",
        json=pickup_payload(scheduled_date="2026-04-01", scheduled_time="12:00"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "SCHEDULED_TIME_IN_PAST"


# ---------------------------------------------------------------------------
# ORD-08  Unavailable menu item → 422 INVALID_MENU_ITEM
# ---------------------------------------------------------------------------


@pytest.fixture
async def unavailable_item():
    """Insert a temporarily unavailable menu item; clean up afterwards."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO menu_items
              (id, location_id, name, description, price, image_url, category,
               allergens, is_vegetarian, is_available, catering_available, display_order)
            VALUES
              ('test-unavailable', '00000000-0000-0000-0000-000000000001',
               'Test Item', 'Temp item for tests', 9.99, '/images/test.jpg',
               'mains', '{}', true, false, false, 99)
            """)
    yield
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM menu_items WHERE id = 'test-unavailable'")


@pytest.mark.anyio
async def test_unavailable_menu_item_returns_422(client, unavailable_item):
    response = await client.post(
        "/api/orders",
        json=pickup_payload(
            items=[{"menu_item_id": "test-unavailable", "quantity": 1}]
        ),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "INVALID_MENU_ITEM"


# ---------------------------------------------------------------------------
# ORD-09  Unknown menu item ID → 422 INVALID_MENU_ITEM
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_unknown_menu_item_returns_422(client):
    response = await client.post(
        "/api/orders",
        json=pickup_payload(items=[{"menu_item_id": "does-not-exist", "quantity": 1}]),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "INVALID_MENU_ITEM"


# ---------------------------------------------------------------------------
# ORD-10  Delivery zip not in an active zone → 422 ZIP_NOT_COVERED
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delivery_zip_not_covered_returns_422(client):
    response = await client.post(
        "/api/orders",
        json=delivery_payload(delivery_zip="99999"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "ZIP_NOT_COVERED"


# ---------------------------------------------------------------------------
# ORD-11  Delivery subtotal below minimum order ($25) → 422 BELOW_MIN_ORDER
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delivery_below_min_order_returns_422(client):
    # samosa×1 = $5.99 — well below $25 minimum
    response = await client.post(
        "/api/orders",
        json=delivery_payload(items=[{"menu_item_id": "samosa", "quantity": 1}]),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "BELOW_MIN_ORDER"


# ---------------------------------------------------------------------------
# ORD-12  Delivery order missing zip → 422 VALIDATION_ERROR
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delivery_missing_zip_returns_422(client):
    payload = delivery_payload()
    del payload["delivery_zip"]
    response = await client.post("/api/orders", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# ORD-13  Delivery order missing address → 422 VALIDATION_ERROR
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delivery_missing_address_returns_422(client):
    payload = delivery_payload()
    del payload["delivery_address"]
    response = await client.post("/api/orders", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# ORD-14  Empty items array → 422 VALIDATION_ERROR
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_missing_items_returns_422(client):
    response = await client.post("/api/orders", json=pickup_payload(items=[]))
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# ORD-15  Invalid order_type value → 422 VALIDATION_ERROR
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_invalid_order_type_returns_422(client):
    response = await client.post(
        "/api/orders",
        json=pickup_payload(order_type="dine_in"),
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# ORD-16  Item quantity of 0 → 422 VALIDATION_ERROR
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_invalid_quantity_returns_422(client):
    response = await client.post(
        "/api/orders",
        json=pickup_payload(items=[{"menu_item_id": "samosa", "quantity": 0}]),
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# ORD-17  Idempotency — duplicate key returns original response, no new record
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_idempotency_duplicate_key_returns_original(client):
    shared_key = str(uuid.uuid4())
    payload = pickup_payload(idempotency_key=shared_key)

    # First submission — should create the order
    first = await client.post("/api/orders", json=payload)
    assert first.status_code == 201
    first_ref = first.json()["reference_number"]

    # Second submission — same idempotency_key, should return original
    second = await client.post("/api/orders", json=payload)
    assert second.status_code == 200
    assert second.json()["reference_number"] == first_ref

    # Confirm only one order record exists in the DB
    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM orders WHERE idempotency_key = $1",
            uuid.UUID(shared_key),
        )
    assert count == 1


# ---------------------------------------------------------------------------
# ORD-18  DB failure → 503 DB_UNAVAILABLE
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_db_failure_returns_503(client, monkeypatch):
    import routers.orders as orders_router

    async def mock_create_order(*args, **kwargs):
        raise Exception("Simulated DB failure")

    monkeypatch.setattr(orders_router, "create_order", mock_create_order)

    response = await client.post("/api/orders", json=pickup_payload())
    assert response.status_code == 503
    assert response.json().get("code") == "DB_UNAVAILABLE"
