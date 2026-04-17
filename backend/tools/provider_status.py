import httpx
from core.config import settings

# Both use statuspage.io format: {"status": {"indicator": "none", "description": "All Systems Operational"}}


async def check_provider_status(provider: str):
    urls = {
        "resend": settings.resend_status_url,
        "twilio": settings.twilio_status_url,
    }

    if provider not in urls:
        return {"provider": provider, "status": "error", "error": f"Unknown provider: {provider}"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(urls[provider], timeout=10)
        data = response.json()
        status = data["status"]["description"]
        return {"provider": provider, "status": status}
    except Exception as e:
        return {"provider": provider, "status": "unreachable", "error": str(e)}
