import httpx
from core.config import settings


async def get_render_logs(lines: int = 100):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.render_api_base_url + "/logs",
                headers={"Authorization": f"Bearer {settings.render_api_key}"},
                params={
                    "ownerId": settings.render_owner_id,
                    "resource": settings.render_service_id,
                    "limit": lines,
                },
            )
        if response.status_code != 200:
            return {"status": "error", "http_code": response.status_code}

        raw = response.json()
        return [
            {
                "timestamp": entry["timestamp"],
                "level": next(
                    (l["value"] for l in entry.get("labels", []) if l["name"] == "level"),
                    "unknown",
                ),
                "message": entry["message"],
            }
            for entry in raw.get("logs", [])
        ]
    except httpx.RequestError as e:
        return {"status": "unreachable", "error": str(e)}
