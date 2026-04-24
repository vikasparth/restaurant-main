# Tests for Slice 2 — Delivery Validation (Read)
# Spec: backend/specs/slice1_menu.md
# TDD: all tests written first — they will all FAIL until the menu endpoint is built.
#
# Run with: pytest tests/test_menu.py -v
# All tests use the real FastAPI app + real test database via httpx.AsyncClient (from conftest.py)

import pytest


@pytest.mark.anyio
async def test_valid_zip_returns_covered(client):
    response = await client.post("/api/delivery/validate", json={"zip_code": "98004"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_covered"] is True
    assert body["city"] == "Bellevue"


@pytest.mark.anyio
async def test_invalid_zip_returns_not_covered(client):
    response = await client.post("/api/delivery/validate", json={"zip_code": "99999"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_covered"] is False
    assert body["city"] is None


@pytest.mark.anyio
async def test_empty_zip_returns_422(client):
    response = await client.post("/api/delivery/validate", json={"zip_code": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_zip_returns_422(client):
    response = await client.post("/api/delivery/validate", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_zip_is_trimmed(client):
    response = await client.post(
        "/api/delivery/validate", json={"zip_code": "  98004  "}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_covered"] is True


@pytest.fixture
async def inactive_zone():
    from core.database import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO delivery_zones (location_id, zip_code, city, is_active)
            VALUES ('00000000-0000-0000-0000-000000000001', '00000', 'TestCity', false)
            """)
    yield
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM delivery_zones WHERE zip_code = '00000'")


@pytest.mark.anyio
async def test_inactive_zone_not_covered(client, inactive_zone):
    response = await client.post("/api/delivery/validate", json={"zip_code": "00000"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_covered"] is False
    assert body["city"] is None


@pytest.mark.anyio
async def test_db_failure_returns_503(client, monkeypatch):
    import services.delivery_service as delivery_service

    async def mock_validate_zip(*args, **kwargs):
        raise Exception("Simulated DB failure")

    monkeypatch.setattr(delivery_service, "validate_zip", mock_validate_zip)

    response = await client.post("/api/delivery/validate", json={"zip_code": "98004"})
    assert response.status_code == 503
    body = response.json()
    assert body.get("code") == "DB_UNAVAILABLE"
