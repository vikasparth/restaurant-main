import os
import requests

from agents.config import FRONTEND_SENTRY_MAX_TURNS, FRONTEND_SENTRY_MAX_TOKENS, SENTRY_API_BASE


def query_sentry_errors(project_slug: str) -> list[dict]:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    org = os.environ["SENTRY_ORG_SLUG"]
    url = f"{SENTRY_API_BASE}/projects/{org}/{project_slug}/issues/"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"query": "is:unresolved", "limit": 25},
    )
    response.raise_for_status()
    return response.json()

def get_stack_trace(issue_id: str) -> dict:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    url = f"{SENTRY_API_BASE}/issues/{issue_id}/events/latest/"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()

def get_affected_releases(issue_id: str) -> list[str]:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    url = f"{SENTRY_API_BASE}/issues/{issue_id}/tags/release/"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    data = response.json()
    return [entry["value"] for entry in data.get("topValues", [])]

TOOLS = [
    {
        "name": "query_sentry_errors",
        "description": "Fetch unresolved error issues from the Sentry frontend project. Call this first to get the list of active errors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_slug": {
                    "type": "string",
                    "description": "The Sentry project slug for the frontend project.",
                }
            },
            "required": ["project_slug"],
        },
    },
    {
        "name": "get_stack_trace",
        "description": "Fetch the latest event and full stack trace for a specific Sentry issue ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "string",
                    "description": "The Sentry issue ID to fetch the stack trace for.",
                }
            },
            "required": ["issue_id"],
        },
    },
    {
        "name": "get_affected_releases",
        "description": "Fetch the list of release SHAs that a Sentry issue has been seen in.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "string",
                    "description": "The Sentry issue ID to fetch affected releases for.",
                }
            },
            "required": ["issue_id"],
        },
    },
]
