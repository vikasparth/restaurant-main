import os
import httpx

BASE_URL = os.environ.get("API_BASE_URL", "https://restaurant-main.onrender.com")


def test_menu_available():
    response = httpx.get(f"{BASE_URL}/api/menu")
    assert response.status_code == 200
    body = response.json()
    assert "categories" in body
    assert isinstance(body["categories"], list)
    assert len(body["categories"]) > 0
