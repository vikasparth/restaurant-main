import httpx
from core.config import settings

async def get_recent_commits(count: int=5):
    try:
        if settings.github_token:
            headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "X-GitHub-Api-Version": settings.github_api_version
            }
        else:
            headers = {"X-GitHub-Api-Version": settings.github_api_version}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{settings.github_api_base_url}/repos/{settings.github_repo}/commits",
                headers=headers,
                params={"per_page":count}
                )
            if response.status_code == 200:
                return response.json()
            else:
                return {"status":"error","http_code":response.status_code,"detail":response.text}
 
    except httpx.RequestError as e:
        return {"status":"unreachable","http_code":None,"error":str(e)}

