import httpx
from core.config import settings

async def check_provider_status(provider: str):
    urls = {
        "resend": settings.resend_status_url,
        "twilio": settings.twilio_status_url,
    }

    if provider not in urls:
        return {"status": "error", "error": f"Unknown provider: {provider}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(urls[provider])
        return {"provider": provider, "raw_status": response.text}
    except httpx.RequestError as e:
        return {"status": "unreachable", "error": str(e)}