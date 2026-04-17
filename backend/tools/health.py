import httpx
from core.config import settings

async def check_health_endpoint():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.production_url+"/health")
        if response.status_code == 200:        
            return {"status":"reachable","http_code":response.status_code}
        else:
            return {"status":"unreachable","http_code":response.status_code}
    except httpx.RequestError as e:
        return {"status":"unreachable","http_code":None,"error":str(e)}
