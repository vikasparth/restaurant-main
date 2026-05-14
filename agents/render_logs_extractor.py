from agents.config import (
    RENDER_API_BASE, RENDER_SERVICE_ID, RENDER_API_KEY,
    RENDER_LOG_FETCH_LIMIT, RENDER_MAX_DISTINCT_ERRORS, RENDER_LOG_MAX_MSG_LEN,
    STATUS_COMPLETED, STATUS_NO_DATA,STATUS_INJECTION_DETECTED,
)
from agents.sentry_utils import record_agent_run
from agents.patterns import _INJECTION_RE
import requests
from datetime import datetime, timezone, timedelta



def run(guardrails: dict, issue_number: str = "") -> dict:
    # empty — pure Python extractor makes zero Claude API calls, no tokens to track
    usage_by_turn = []
    end_time = datetime.now(timezone.utc)
    hours = guardrails.get("time_window", 1)
    start_time = end_time - timedelta(hours=hours)
    url = f"{RENDER_API_BASE}/services/{RENDER_SERVICE_ID}/logs"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
        params={
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "limit": RENDER_LOG_FETCH_LIMIT,
        },
    )
    logs = response.json().get("logs", [])

    # injection check runs before any filtering — adversarial content must never reach the Orchestrator
    for log in logs:
        if _INJECTION_RE.search(log.get("message", "")):
            result = {"status": STATUS_INJECTION_DETECTED, "source": "render-api"}
            record_agent_run("render-logs", result, usage_by_turn, issue_number)
            return result

    # deploy lines are Render infrastructure noise, not runtime errors
    errors = [
        log for log in logs
        if log.get("type") == "app"
        and log.get("level") in ("error", "warn")
    ]

    # group identical messages so the Recommendation Agent sees frequency, not raw repetition
    deduped = {}
    for entry in errors:
        key = entry.get("message", "")
        if key in deduped:
            deduped[key]["count"] += 1
        else:
            deduped[key] = {**entry, "count": 1}
    errors = list(deduped.values())

    # highest-count errors first; cap at RENDER_MAX_DISTINCT_ERRORS so the combined Orchestrator
    # payload stays under the ~3,000 token budget — low-frequency errors are least likely root causes
    errors = sorted(errors, key=lambda e: e["count"], reverse=True)[:RENDER_MAX_DISTINCT_ERRORS]

    if not errors:
        result = {"status": STATUS_NO_DATA, "source": "render-api"}
        record_agent_run("render-logs", result, usage_by_turn, issue_number)
        return result

    result = {
        "status": STATUS_COMPLETED,
        "source": "render-api",
        "log_window": {"from": start_time.isoformat(), "to": end_time.isoformat()},
        "error_count": len(errors),
        "errors": errors,
        "injection_flag": False,
        "pii_flag": False,
    }
    record_agent_run("render-logs", result, usage_by_turn, issue_number)
    return result
