import requests

from agents.config import (
    SENTRY_QUERY_LIMIT,
    SENTRY_STACK_FRAME_LIMIT,
    SENTRY_WINDOW_LADDER,
    STATUS_COMPLETED,
    STATUS_INJECTION_DETECTED,
    STATUS_INVALID_INPUT,
    STATUS_NETWORK_ERROR,
    STATUS_NOT_FOUND,
    STATUS_NO_DATA,
    STATUS_RATE_LIMITED,
    STATUS_SCHEMA_ERROR,
    STATUS_SERVER_ERROR,
    STATUS_TIMEOUT,
    STATUS_UNAUTHENTICATED,
    STATUS_UNAUTHORIZED,
)
from agents.sentry_api import (
    _contains_pii,
    _looks_like_injection,
    _pick_issue,
    _validate_sentry_guardrails,
    get_affected_releases,
    get_stack_trace,
    query_sentry_errors,
)
from agents.sentry_utils import record_agent_run

# why: hardcoded — this extractor owns exactly one Sentry project; the Orchestrator
# passes guardrails (time window, limits) but cannot redirect to a different project
_PROJECT_SLUG = "restaurant-frontend"
_SOURCE = "sentry-frontend"


def _error_result(status: str) -> dict:
    return {"status": status, "source": _SOURCE}


def run(guardrails: dict, issue_number: str = "") -> dict:
    # why: empty list — no Claude API calls, nothing to measure; passed to
    # record_agent_run so the observability contract is satisfied uniformly
    usage_by_turn = []

    if _validate_sentry_guardrails(guardrails):
        result = _error_result(STATUS_INVALID_INPUT)
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result

    max_issues = guardrails.get("max_issues", SENTRY_QUERY_LIMIT)
    max_frames = guardrails.get("max_frames", SENTRY_STACK_FRAME_LIMIT)

    try:
        for window in SENTRY_WINDOW_LADDER:
            issues = query_sentry_errors(_PROJECT_SLUG, window, max_issues)
            if not issues:
                continue

            issue = _pick_issue(issues)

            # why: id is required for follow-up calls to get_stack_trace and
            # get_affected_releases — a missing id means the API returned an
            # unexpected shape and we cannot safely continue
            if not issue.get("id"):
                result = _error_result(STATUS_SCHEMA_ERROR)
                record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
                return result

            if _looks_like_injection(issue):
                result = {
                    "status": STATUS_INJECTION_DETECTED,
                    "source": _SOURCE,
                    "time_window": window,
                }
                record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
                return result

            stack = get_stack_trace(issue["id"], max_frames)
            releases = get_affected_releases(issue["id"])

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
            }
            record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
            return result

        result = _error_result(STATUS_NO_DATA)
        result["source"] = _SOURCE  # _error_result already sets source, kept explicit
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result

    except KeyError:
        # why: KeyError means a required env var (SENTRY_AUTH_TOKEN or SENTRY_ORG_SLUG)
        # is missing — treat as unauthenticated so the Orchestrator can alert the owner
        result = _error_result(STATUS_UNAUTHENTICATED)
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result

    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else 0
        if code == 401:
            status = STATUS_UNAUTHENTICATED
        elif code == 403:
            status = STATUS_UNAUTHORIZED
        elif code == 404:
            status = STATUS_NOT_FOUND
        elif code == 429:
            status = STATUS_RATE_LIMITED
        else:
            status = STATUS_SERVER_ERROR
        result = _error_result(status)
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result

    except requests.exceptions.Timeout:
        result = _error_result(STATUS_TIMEOUT)
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result

    except requests.exceptions.ConnectionError:
        result = _error_result(STATUS_NETWORK_ERROR)
        record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
        return result
