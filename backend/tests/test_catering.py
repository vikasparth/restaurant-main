# Tests for Slice 5 — Catering Orders
# Spec: backend/specs/slice5_catering.md
# TDD: all tests written first — they will all FAIL until the endpoint is built.
#
# Run with: pytest tests/test_catering.py -v

import uuid
from datetime import date, timedelta

import pytest

from core.database import get_pool

# Event date always 60 days out — stays valid as time passes
_future = date.today() + timedelta(days=60)
VALID_EVENT_DATE = _future.strftime("%Y-%m-%d")
VALID_EVENT_TIME = "18:00"

# Prices come from seed data (20260406000002_seed_data.sql)
# butter-chicken: $85/tray  catering_available=true
# samosa:         $35/tray  catering_available=true
# garlic-naan:    $25/tray  catering_available=true  (used for below-minimum test)
# mango-lassi:    null      catering_available=false  (used for non-catering test)


def catering_payload(**overrides) -> dict:
    """Minimal valid catering order. butter-chicken($85) + samosa($35) = $120 total."""
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Priya Sharma",
        "customer_email": "priya@example.com",
        "customer_phone": "4255550123",
        "event_date": VALID_EVENT_DATE,
        "event_time": VALID_EVENT_TIME,
        "delivery_address": "123 Main St, Bellevue, WA 98004",
        "zip_code": "98004",
        "items": [
            {"item_id": "butter-chicken", "trays": 1},  # $85
            {"item_id": "samosa", "trays": 1},  # $35
        ],
    }
    base.update(overrides)
    return base


@pytest.mark.anyio
async def test_valid_catering_order_returns_201(client):
    response = await client.post("/api/catering", json=catering_payload())
    assert response.status_code == 201
    body = response.json()
    assert "reference_number" in body
    assert body["status"] == "confirmed"
    assert "total_amount" in body
    assert "deposit_amount" in body
    assert body["event_date"] == VALID_EVENT_DATE
    assert body["event_time"] == VALID_EVENT_TIME


@pytest.mark.anyio
async def test_idempotency_duplicate_key_returns_200(client):
    shared_key = str(uuid.uuid4())
    payload = catering_payload(idempotency_key=shared_key)

    first = await client.post("/api/catering", json=payload)
    assert first.status_code == 201
    first_ref = first.json()["reference_number"]

    second = await client.post("/api/catering", json=payload)
    assert second.status_code == 200
    assert second.json()["reference_number"] == first_ref

    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM catering_orders WHERE idempotency_key = $1",
            uuid.UUID(shared_key),
        )
    assert count == 1


@pytest.mark.anyio
async def test_event_less_than_48h_returns_422(client):
    # 2026-04-12 is today — well within the 48h window
    response = await client.post(
        "/api/catering",
        json=catering_payload(event_date="2026-04-12", event_time="20:00"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "LESS_THAN_48_HOURS"


@pytest.mark.anyio
async def test_below_min_order_returns_422(client):
    # 1 tray of garlic-naan = $25 — below the $100 minimum
    response = await client.post(
        "/api/catering",
        json=catering_payload(items=[{"item_id": "garlic-naan", "trays": 1}]),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "BELOW_MIN_CATERING_ORDER"


@pytest.mark.anyio
async def test_invalid_item_id_returns_422(client):
    response = await client.post(
        "/api/catering",
        json=catering_payload(items=[{"item_id": "does-not-exist", "trays": 2}]),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "INVALID_MENU_ITEM"


@pytest.mark.anyio
async def test_non_catering_item_returns_422(client):
    # mango-lassi has catering_available=false in seed data
    response = await client.post(
        "/api/catering",
        json=catering_payload(
            items=[
                {"item_id": "mango-lassi", "trays": 1},
                {"item_id": "butter-chicken", "trays": 2},
            ]
        ),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "ITEM_NOT_CATERING_AVAILABLE"


@pytest.mark.anyio
async def test_empty_items_returns_422(client):
    response = await client.post("/api/catering", json=catering_payload(items=[]))
    assert response.status_code == 422


@pytest.mark.anyio
async def test_total_and_deposit_amounts_correct(client):
    # butter-chicken $85 + samosa $35 = $120 total; 40% deposit = $48.00
    response = await client.post("/api/catering", json=catering_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["total_amount"] == 120.00
    assert body["deposit_amount"] == 48.00


@pytest.mark.anyio
async def test_order_saved_to_both_tables(client):
    response = await client.post("/api/catering", json=catering_payload())
    assert response.status_code == 201
    ref = response.json()["reference_number"]

    pool = get_pool()
    async with pool.acquire() as conn:
        order_id = await conn.fetchval(
            "SELECT id FROM catering_orders WHERE reference_number = $1", ref
        )
        assert order_id is not None

        item_count = await conn.fetchval(
            "SELECT COUNT(*) FROM catering_order_items WHERE catering_order_id = $1",
            order_id,
        )
    assert item_count == 2  # butter-chicken + samosa


@pytest.mark.anyio
async def test_zip_not_in_delivery_zone_returns_422(client):
    response = await client.post(
        "/api/catering",
        json=catering_payload(zip_code="00000"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "ZIP_NOT_COVERED"


@pytest.mark.anyio
async def test_missing_customer_email_returns_422(client):
    payload = catering_payload()
    del payload["customer_email"]
    response = await client.post("/api/catering", json=payload)
    assert response.status_code == 422
