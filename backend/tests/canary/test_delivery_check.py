import os
import httpx

BASE_URL = os.environ.get("API_BASE_URL", "https://restaurant-main.onrender.com")


def test_delivery_check():
    response = httpx.post(
        f"{BASE_URL}/api/delivery/validate",
        json={"zip_code": "98004"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_covered"] is True
