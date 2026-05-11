import os

import requests

from agents.config import (
    SENTRY_API_BASE,
    SENTRY_QUERY_LIMIT,
    SENTRY_STACK_FRAME_LIMIT,
    SENTRY_WINDOW_LADDER,
    STATUS_COMPLETED,
    STATUS_INJECTION_DETECTED,
    STATUS_NO_DATA,
)
from agents.sentry_api import (
    _contains_pii,
    _looks_like_injection,
    _pick_issue,
    get_affected_releases,
    get_stack_trace,
    query_sentry_errors,
)
from agents.sentry_utils import record_agent_run

# why: hardcoded — this extractor owns exactly one Sentry project; the Orchestrator
# passes guardrails (time window, limits) but cannot redirect to a different project
_PROJECT_SLUG = "restaurant-backend"
_SOURCE = "sentry-backend"


def _get_status_code(issue_id: str) -> int:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    # why: fetches raw event to read HTTP status tag — get_stack_trace does not
    # return tags, so a separate call is needed without modifying the shared helper
    url = f"{SENTRY_API_BASE}/issues/{issue_id}/events/latest/"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    data = response.json()
    for tag in data.get("tags", []):
        if tag.get("key") == "status_code":
            return int(tag["value"])
    return 0


def run(guardrails: dict, issue_number: str = "") -> dict:
    # why: empty list — no Claude API calls, nothing to measure; passed to
    # record_agent_run so the observability contract is satisfied uniformly
    usage_by_turn = []
    max_issues = guardrails.get("max_issues", SENTRY_QUERY_LIMIT)
    max_frames = guardrails.get("max_frames", SENTRY_STACK_FRAME_LIMIT)

    for window in SENTRY_WINDOW_LADDER:
        issues = query_sentry_errors(_PROJECT_SLUG, window, max_issues)
        if not issues:
            continue

        issue = _pick_issue(issues)

        if _looks_like_injection(issue):
            result = {
                "status": STATUS_INJECTION_DETECTED,
                "source": _SOURCE,
                "time_window": window,
            }
            record_agent_run("backend-sentry", result, usage_by_turn, issue_number)
            return result

        stack = get_stack_trace(issue["id"], max_frames)
        releases = get_affected_releases(issue["id"])
        status_code = _get_status_code(issue["id"])

        result = {
            "status": STATUS_COMPLETED,
            "source": _SOURCE,
            "time_window": window,
            "pii_flag": _contains_pii(issue),
            "injection_flag": False,
            **issue,
            **stack,
            # why: only the most recent release SHA — Orchestrator passes it to
            # GitHub Extractor for regression correlation
            "releases": releases[:1],
            "endpoint": issue["culprit"],
            "status_code": status_code,
        }
        record_agent_run("backend-sentry", result, usage_by_turn, issue_number)
        return result

    result = {"status": STATUS_NO_DATA, "source": _SOURCE}
    record_agent_run("backend-sentry", result, usage_by_turn, issue_number)
    return result
