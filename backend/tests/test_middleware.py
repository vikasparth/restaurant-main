import asyncio

import pytest


@pytest.mark.anyio
async def test_request_is_logged(client, db):
    response = await client.get("/health")
    await asyncio.sleep(0.1)

    assert response.status_code == 200

    row = await db.fetchrow(
        "SELECT * FROM request_logs WHERE path = $1 ORDER BY created_at DESC LIMIT 1",
        "/health",
    )

    assert row is not None


@pytest.mark.anyio
async def test_request_log_fields(client, db):
    await client.get("/health")
    await asyncio.sleep(0.1)

    row = await db.fetchrow(
        "SELECT * FROM request_logs WHERE path = $1 ORDER BY created_at DESC LIMIT 1",
        "/health",
    )

    assert row["method"] == "GET"
    assert row["status_code"] == 200
    assert row["duration_ms"] >= 0
    assert row["request_id"] != ""


@pytest.mark.anyio
async def test_request_log_captures_error_status(client, db):
    await client.get("/api/nonexistent-endpoint-404")
    await asyncio.sleep(0.1)

    row = await db.fetchrow(
        "SELECT * FROM request_logs WHERE path = $1 ORDER BY created_at DESC LIMIT 1",
        "/api/nonexistent-endpoint-404",
    )

    assert row is not None
    assert row["status_code"] == 404
