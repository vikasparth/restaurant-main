import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from core.database import connect, disconnect
from core.logging import setup_logging
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
async def setup_db():
    setup_logging()
    await connect()
    yield
    await disconnect()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_notifications():
    with patch(
        "services.notification_service.send_email", new_callable=AsyncMock
    ), patch("services.notification_service.send_whatsapp", new_callable=AsyncMock):
        yield


@pytest.fixture
async def db():
    from core.database import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn
