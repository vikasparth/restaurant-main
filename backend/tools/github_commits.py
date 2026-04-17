import httpx
from core.config import settings


async def get_recent_commits(count: int = 5):
    try:
        headers = {"X-GitHub-Api-Version": settings.github_api_version}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{settings.github_api_base_url}/repos/{settings.github_repo}/commits",
                headers=headers,
                params={"per_page": count},
            )
        if response.status_code != 200:
            return {"status": "error", "http_code": response.status_code}

        return [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"].splitlines()[0],
                "author": c["commit"]["author"]["name"],
                "committed_at": c["commit"]["author"]["date"],
            }
            for c in response.json()
        ]
    except httpx.RequestError as e:
        return {"status": "unreachable", "error": str(e)}
