import os
import httpx 

BASE_URL = os.environ.get("API_BASE_URL", "https://restaurant-main.onrender.com")

def test_health_check():
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
