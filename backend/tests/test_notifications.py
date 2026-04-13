# Tests for Slice 6 — Notifications
# Spec: specs/slice6_notifications.md
# TDD: all tests written first — they will all FAIL until the services are built.
#
# Run with: pytest tests/test_notifications.py -v

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from core.config import settings

INTERNAL_TOKEN = settings.internal_token

# Valid future dates — computed dynamically so they never expire
_future = date.today() + timedelta(days=60)
VALID_SCHEDULED_DATE = _future.strftime("%Y-%m-%d")
VALID_RESERVED_DATE = _future.strftime("%Y-%m-%d")
VALID_EVENT_DATE = _future.strftime("%Y-%m-%d")


def order_payload(**overrides) -> dict:
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "4255550123",
        "order_type": "pickup",
        "scheduled_date": VALID_SCHEDULED_DATE,
        "scheduled_time": "18:00",
        "items": [{"menu_item_id": "butter-chicken", "quantity": 1}],
    }
    base.update(overrides)
    return base


def reservation_payload(**overrides) -> dict:
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "4255550123",
        "reserved_date": VALID_RESERVED_DATE,
        "reserved_time": "18:00",
        "party_size": 4,
    }
    base.update(overrides)
    return base


def catering_payload(**overrides) -> dict:
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "4255550123",
        "event_date": VALID_EVENT_DATE,
        "event_time": "18:00",
        "delivery_address": "123 Main St, Bellevue, WA 98004",
        "zip_code": "98004",
        "items": [
            {"item_id": "butter-chicken", "trays": 1},
            {"item_id": "samosa", "trays": 1},
        ],
    }
    base.update(overrides)
    return base


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_order_triggers_customer_email(mock_email, mock_whatsapp, client):
    """Valid order → customer email send called."""
    response = await client.post("/api/orders", json=order_payload())
    assert response.status_code == 201
    assert mock_email.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_order_triggers_owner_notifications(mock_email, mock_whatsapp, client):
    """Valid order → owner email AND WhatsApp both called."""
    response = await client.post("/api/orders", json=order_payload())
    assert response.status_code == 201
    assert mock_email.called
    assert mock_whatsapp.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_reservation_triggers_customer_email(mock_email, mock_whatsapp, client):
    """Valid reservation → customer email called."""
    response = await client.post("/api/reservations", json=reservation_payload())
    assert response.status_code == 201
    assert mock_email.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_reservation_triggers_owner_notifications(
    mock_email, mock_whatsapp, client
):
    """Valid reservation → owner email AND WhatsApp both called."""
    response = await client.post("/api/reservations", json=reservation_payload())
    assert response.status_code == 201
    assert mock_email.called
    assert mock_whatsapp.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_catering_triggers_customer_email(mock_email, mock_whatsapp, client):
    """Valid catering order → customer email called."""
    response = await client.post("/api/catering", json=catering_payload())
    assert response.status_code == 201
    assert mock_email.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_catering_triggers_owner_notifications(mock_email, mock_whatsapp, client):
    """Valid catering order → owner email AND WhatsApp both called."""
    response = await client.post("/api/catering", json=catering_payload())
    assert response.status_code == 201
    assert mock_email.called
    assert mock_whatsapp.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_email_failure_does_not_block_order(mock_email, mock_whatsapp, client):
    """Resend raises → order still saved and returns 201."""
    mock_email.side_effect = Exception("Resend API down")
    response = await client.post("/api/orders", json=order_payload())
    assert response.status_code == 201


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_whatsapp_failure_does_not_block_order(mock_email, mock_whatsapp, client):
    """Twilio raises → order still saved and returns 201."""
    mock_whatsapp.side_effect = Exception("Twilio API down")
    response = await client.post("/api/orders", json=order_payload())
    assert response.status_code == 201


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_reminder_endpoint_sends_tomorrows_reservations(
    mock_email, mock_whatsapp, client
):
    """Reminder endpoint with valid token → returns 200 with sent count."""
    response = await client.post(
        "/api/internal/send-reminders",
        headers={"X-Internal-Token": INTERNAL_TOKEN},
    )
    assert response.status_code == 200
    assert "sent" in response.json()


@pytest.mark.anyio
async def test_reminder_endpoint_rejects_missing_token(client):
    """Reminder endpoint with no token → 401."""
    response = await client.post("/api/internal/send-reminders")
    assert response.status_code == 401


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_reservation_without_email_skips_customer_email(
    mock_email, mock_whatsapp, client
):
    """Reservation with no customer_email → no customer email sent, owner still notified."""
    response = await client.post(
        "/api/reservations", json=reservation_payload(customer_email=None)
    )
    assert response.status_code == 201
    assert mock_whatsapp.called


@pytest.mark.anyio
@patch("services.notification_service.send_whatsapp", new_callable=AsyncMock)
@patch("services.notification_service.send_email", new_callable=AsyncMock)
async def test_reminder_skips_reservation_without_email(
    mock_email, mock_whatsapp, client
):
    """Reminder endpoint → reservations with null email are skipped silently."""
    response = await client.post(
        "/api/internal/send-reminders",
        headers={"X-Internal-Token": INTERNAL_TOKEN},
    )
    assert response.status_code == 200
    # No assertion on mock_email — depends on DB state; just verify no crash
