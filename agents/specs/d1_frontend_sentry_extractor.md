# D.1 Spec — Frontend Sentry Extractor

**Status: Complete (retrospective spec)**
**Execution plan ref:** D.1 — Frontend Sentry Extractor

---

## Goal

A pure Python extractor that queries the `restaurant-frontend` Sentry project for
unresolved errors, picks the highest-severity issue, and returns a structured dict
the Orchestrator can route downstream. Makes no Claude API calls — token cost is zero.
Serves as the reference implementation for all subsequent Sentry extractors (D.2+).

---

## What we are NOT building

- No Claude API calls — pure Python extractor; `usage_by_turn = []`
- No write operations to Sentry or any external system
- No custom logging — observability goes through `record_agent_run` only

---

## Shared helpers — `agents/sentry_api.py`

The following functions are shared across all Sentry extractors and must be imported
from `agents/sentry_api.py`. Do not define them inside an extractor file.

| Function | Signature | Notes |
|---|---|---|
| `query_sentry_errors` | `query_sentry_errors(project_slug: str, window: str, limit: int) -> list[dict]` | Trims to minimum fields only — never returns raw Sentry response |
| `get_stack_trace` | `get_stack_trace(issue_id: str, max_frames: int) -> dict` | Fetches `/events/latest/`; filters to `inApp=True` frames only |
| `get_affected_releases` | `get_affected_releases(issue_id: str) -> list[str]` | Returns release version strings from Sentry tags |
| `_pick_issue` | `_pick_issue(issues: list[dict]) -> dict` | Severity-first, then most recent `last_seen` |
| `_looks_like_injection` | `_looks_like_injection(issue: dict) -> bool` | Checks `title` + `culprit` against prompt injection patterns |
| `_contains_pii` | `_contains_pii(issue: dict) -> bool` | Checks `title` + `culprit` for email/phone patterns |

---

## File — `agents/frontend_sentry_extractor.py`

### Project slug

```python
_PROJECT_SLUG = "restaurant-frontend"
```

Hardcoded — this extractor owns exactly one Sentry project. The Orchestrator passes
guardrails but cannot redirect to a different project.

### `run()` signature

```python
def run(guardrails: dict, issue_number: str = "") -> dict:
```

`issue_number` defaults to `""` so existing callers are not broken when the
Orchestrator passes it later.

### Window escalation logic

```python
for window in SENTRY_WINDOW_LADDER:      # ["age:-1h", "age:-6h", "age:-24h"]
    issues = query_sentry_errors(_PROJECT_SLUG, window, max_issues)
    if not issues:
        continue
    # process and return on first non-empty window
```

Starts at the shortest window and escalates only when zero issues are found.
Once any issue is found the window is locked — never widens further.

### Guard order inside the loop

1. `_looks_like_injection(issue)` — checked first; returns early with `injection_detected`
2. `_contains_pii(issue)` — sets `pii_flag` on the result; does not block

### Return shapes

**Completed run:**
```python
{
    "status": "completed",
    "source": "sentry-frontend",
    "time_window": window,
    "pii_flag": bool,
    "injection_flag": False,
    # all fields from query_sentry_errors (id, title, level, culprit, ...)
    # all fields from get_stack_trace (exception_type, exception_message, top_frames, ...)
    "releases": [str],   # most recent release SHA only — releases[:1]
}
```

**Injection detected (early exit):**
```python
{"status": "injection_detected", "source": "sentry-frontend", "time_window": window}
```

**No data (all windows empty):**
```python
{"status": "no_data", "source": "sentry-frontend"}
```

### Observability

All 3 return paths call `record_agent_run` before returning:
```python
record_agent_run("frontend-sentry", result, usage_by_turn, issue_number)
```

---

## Acceptance Criteria

### Scenario 2 — Render cold start (`render-cold-start-503`)

Trigger: frontend Sentry captures 503 network errors on API calls.

The extractor must return a `completed` dict containing:
```python
{
    "status": "completed",
    "source": "sentry-frontend",
    "exception_type": "NetworkError",   # or equivalent
    "level": "error",
}
```

### Scenario 5 — Schema drift (`graphql-schema-resolver-drift`)

Trigger: frontend Sentry captures a GraphQL field resolution error.

The extractor must return a `completed` dict containing:
```python
{
    "status": "completed",
    "source": "sentry-frontend",
}
```

For scenarios where no frontend Sentry errors exist (Scenario 1, 4), the extractor
must return `{"status": "no_data", "source": "sentry-frontend"}` cleanly.

---

## TDD Tests — `agents/tests/test_frontend_sentry_extractor.py`

| # | Test name | What it asserts |
|---|---|---|
| 1 | `test_frontend_sentry_returns_structured_findings_on_active_error` | `status=completed`, all required fields present |
| 2 | `test_frontend_sentry_escalates_window_when_first_window_empty` | `time_window=age:-6h` when first window empty |
| 3 | `test_frontend_sentry_returns_no_data_when_all_windows_empty` | `status=no_data`, `source=sentry-frontend` |
| 4 | `test_frontend_sentry_detects_injection_in_error_title` | `status=injection_detected` |

All tests mock `query_sentry_errors`, `get_stack_trace`, `get_affected_releases`,
and `record_agent_run` at `agents.frontend_sentry_extractor.*` — patch where the
name is used, not where it is defined.

---

## Dependencies

| Symbol | Source |
|---|---|
| `query_sentry_errors`, `get_stack_trace`, `get_affected_releases`, `_pick_issue`, `_looks_like_injection`, `_contains_pii` | `agents/sentry_api.py` |
| `record_agent_run` | `agents/sentry_utils.py` |
| `SENTRY_WINDOW_LADDER`, `SENTRY_QUERY_LIMIT`, `SENTRY_STACK_FRAME_LIMIT` | `agents/config.py` |
