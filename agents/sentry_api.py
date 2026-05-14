# Sentry REST API client — shared query helpers used by all Sentry extractors.
# Owns the HTTP calls to the Sentry API and the data-vetting logic (PII detection,
# injection guards, issue selection). Import from here; never define these in an
# extractor file or you create a cross-feature dependency.
import os
import requests

from agents.config import SENTRY_API_BASE
from agents.patterns import _INJECTION_RE, _EMAIL_RE, _PHONE_RE

# why: fatal=0 so sorted() puts it first; missing levels default to lowest priority
_LEVEL_PRIORITY = {"fatal": 0, "error": 1, "warning": 2, "info": 3}


def query_sentry_errors(project_slug: str, window: str, limit: int) -> list[dict]:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    org = os.environ["SENTRY_ORG_SLUG"]
    url = f"{SENTRY_API_BASE}/projects/{org}/{project_slug}/issues/"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"query": f"is:unresolved {window}", "limit": limit},
    )
    # why: raises immediately on 4xx/5xx — without this a 401 returns a JSON error
    # body that would be silently passed to the Orchestrator as valid data
    response.raise_for_status()
    return [
        {
            "id": issue["id"],
            "title": issue.get("title", ""),
            "level": issue.get("level", "error"),
            "culprit": issue.get("culprit", ""),
            "count": issue.get("count", 0),
            "user_count": issue.get("userCount", 0),
            "is_unhandled": issue.get("isUnhandled", False),
            "first_seen": issue.get("firstSeen", ""),
            "last_seen": issue.get("lastSeen", ""),
            # why: firstRelease may be None on projects without release tagging
            "release": (issue.get("firstRelease") or {}).get("version"),
        }
        for issue in response.json()
    ]


def get_stack_trace(issue_id: str, max_frames: int) -> dict:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    # why: /events/latest/ fetches the most recent occurrence — stack traces evolve
    # as code changes; the oldest event may point to a line that no longer exists
    url = f"{SENTRY_API_BASE}/issues/{issue_id}/events/latest/"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    data = response.json()
    exception_values = (
        data.get("entries", [{}])[0].get("data", {}).get("values", [{}])
    )
    exc = exception_values[0] if exception_values else {}
    frames = exc.get("stacktrace", {}).get("frames", [])
    # why: inApp=True filters to app code only — framework/library frames (React
    # internals, node_modules) never point to the root cause and waste tokens
    app_frames = [f for f in frames if f.get("inApp", False)]
    top_frames = [
        {
            "filename": f.get("filename", ""),
            "lineno": f.get("lineNo", ""),
            "function": f.get("function", ""),
        }
        for f in app_frames[-max_frames:]
    ]
    return {
        "exception_type": exc.get("type", ""),
        "exception_message": exc.get("value", ""),
        "culprit": data.get("culprit", ""),
        "top_frames": top_frames,
    }


def get_affected_releases(issue_id: str) -> list[str]:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    url = f"{SENTRY_API_BASE}/issues/{issue_id}/tags/release/"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    data = response.json()
    # why: topValues is absent (not null) when no releases are tagged
    return [entry["value"] for entry in data.get("topValues", [])]


def _pick_issue(issues: list[dict]) -> dict:
    by_severity = sorted(
        issues, key=lambda i: _LEVEL_PRIORITY.get(i.get("level", "info"), 3)
    )
    top_level = by_severity[0].get("level", "info")
    same_level = [i for i in by_severity if i.get("level", "info") == top_level]
    # why: ISO 8601 strings sort lexicographically — largest string = most recent
    return max(same_level, key=lambda i: i.get("last_seen", ""))


def _validate_sentry_guardrails(guardrails: dict) -> str | None:
    # why: bool is a subclass of int in Python — must exclude it explicitly
    for key in ("max_issues", "max_frames"):
        val = guardrails.get(key)
        if val is not None and (isinstance(val, bool) or not isinstance(val, int) or val <= 0):
            return f"{key} must be a positive integer"
    return None


def _looks_like_injection(issue: dict) -> bool:
    text = f"{issue.get('title', '')} {issue.get('culprit', '')}"
    return bool(_INJECTION_RE.search(text))


def _contains_pii(issue: dict) -> bool:
    text = f"{issue.get('title', '')} {issue.get('culprit', '')}"
    return bool(_EMAIL_RE.search(text) or _PHONE_RE.search(text))
