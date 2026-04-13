# Tests for Slice 4 — Reservations
# Spec: specs/slice4_reservations.md
# TDD: all tests written first — they will all FAIL until the endpoint is built.
#
# Run with: pytest tests/test_reservations.py -v

import re
import uuid
from datetime import date, timedelta

import pytest

from core.database import get_pool

_future    = date.today() + timedelta(days=60)  # always well in the future
VALID_DATE = _future.strftime("%Y-%m-%d")
VALID_TIME = "18:00"

def reservation_payload(**overrides) -> dict:
    """Minimal valid reservation. 4 guests on a Wednesday evening."""
    base = {
        "idempotency_key":  str(uuid.uuid4()),
        "customer_name":    "Priya Sharma",
        "customer_email":   "priya@example.com",
        "customer_phone":   "4255550123",
        "party_size":       4,
        "reserved_date":    VALID_DATE,
        "reserved_time":    VALID_TIME,
    }
    base.update(overrides)
    return base

@pytest.mark.anyio
async def test_valid_reservation_returns_201(client):
    response = await client.post("/api/reservations", json=reservation_payload())
    assert response.status_code == 201
    body = response.json()
    assert "reference_number" in body
    assert body["status"] == "confirmed"
    assert body["party_size"] == 4

@pytest.mark.anyio
async def test_reference_number_format(client):
    response = await client.post("/api/reservations", json=reservation_payload())
    assert response.status_code == 201
    ref = response.json()["reference_number"]
    assert re.fullmatch(r"AKR-\d{8}-\d{4}", ref), f"Unexpected format: {ref}"

@pytest.mark.anyio
async def test_scheduled_time_outside_hours_returns_422(client):
    response = await client.post(
        "/api/reservations",
        json=reservation_payload(reserved_time="23:00"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "OUTSIDE_HOURS"

@pytest.mark.anyio
async def test_scheduled_time_in_past_returns_422(client):
    response = await client.post(
        "/api/reservations",
        json=reservation_payload(reserved_date="2026-04-01", reserved_time="12:00"),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "SCHEDULED_TIME_IN_PAST"

@pytest.mark.anyio
async def test_party_size_exceeded_returns_422(client):
    response = await client.post(
        "/api/reservations",
        json=reservation_payload(party_size=21),
    )
    assert response.status_code == 422
    assert response.json().get("code") == "PARTY_SIZE_EXCEEDED"

@pytest.mark.anyio
async def test_invalid_party_size_returns_422(client):
    response = await client.post(
        "/api/reservations",
        json=reservation_payload(party_size=0),
    )
    assert response.status_code == 422

@pytest.mark.anyio
async def test_missing_phone_returns_422(client):
    payload = reservation_payload()
    del payload["customer_phone"]
    response = await client.post("/api/reservations", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_idempotency_duplicate_key_returns_original(client):
    shared_key = str(uuid.uuid4())
    payload = reservation_payload(idempotency_key=shared_key)

    first = await client.post("/api/reservations", json=payload)
    assert first.status_code == 201
    first_ref = first.json()["reference_number"]

    second = await client.post("/api/reservations", json=payload)
    assert second.status_code == 200
    assert second.json()["reference_number"] == first_ref

    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM reservations WHERE idempotency_key = $1",
            uuid.UUID(shared_key),
        )
    assert count == 1

@pytest.mark.anyio
async def test_notes_stored_in_db(client):
    note_text = "Window table please"
    response = await client.post(
        "/api/reservations",
        json=reservation_payload(notes=note_text),
    )
    assert response.status_code == 201
    ref = response.json()["reference_number"]

    pool = get_pool()
    async with pool.acquire() as conn:
        notes = await conn.fetchval(
            "SELECT notes FROM reservations WHERE reference_number = $1",
            ref,
        )
    assert notes == note_text

@pytest.mark.anyio
async def test_db_failure_returns_503(client, monkeypatch):
    import routers.reservations as reservations_router

    async def mock_create_reservation(*args, **kwargs):
        raise Exception("Simulated DB failure")

    monkeypatch.setattr(reservations_router, "create_reservation", mock_create_reservation)

    response = await client.post("/api/reservations", json=reservation_payload())
    assert response.status_code == 503
    assert response.json().get("code") == "DB_UNAVAILABLE"

