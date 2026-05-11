# D.2 Spec — Backend Sentry Extractor

**Status: Awaiting sign-off**
**Execution plan ref:** D.2 — Backend Sentry Extractor

---

## Goal

A pure Python extractor that queries the `restaurant-backend` Sentry project for
unresolved errors, picks the highest-severity issue, and returns a structured dict
the Orchestrator can route downstream. Mirrors D.1 (`frontend_sentry_extractor.py`)
exactly — same window ladder, same guards, same `run()` contract — with two
additional return fields: `endpoint` and `status_code`.

---

## What we are NOT building

- No Claude API calls — this is a pure Python extractor; `usage_by_turn = []`
- No new config constants — reuse `SENTRY_WINDOW_LADDER`, `SENTRY_QUERY_LIMIT`,
  `SENTRY_STACK_FRAME_LIMIT` from `agents/config.py`

---

## Step 1 — Refactor: extract shared helpers into `agents/sentry_api.py`

`query_sentry_errors`, `get_stack_trace`, `get_affected_releases`, `_pick_issue`,
`_looks_like_injection`, and `_contains_pii` currently live in
`frontend_sentry_extractor.py`. D.2 needs the same functions — having
`backend_sentry_extractor.py` import from `frontend_sentry_extractor.py` would be
a bad cross-module dependency.

Move all 6 into a new `agents/sentry_api.py`. Then update
`frontend_sentry_extractor.py` to import from `sentry_api` instead of defining
them locally. No logic changes — move only.

**Affected files:**
- `agents/sentry_api.py` — new file, contains the 6 moved functions
- `agents/frontend_sentry_extractor.py` — remove the 6 definitions, add imports from `sentry_api`
- `agents/tests/test_frontend_sentry_extractor.py` — update mock patch paths from
  `agents.frontend_sentry_extractor.query_sentry_errors` →
  `agents.sentry_api.query_sentry_errors` (and same for the other mocked functions)

Run the full test suite after this refactor — all 10 tests must stay green before
moving to Step 2.

---

## Step 2 — New file: `agents/backend_sentry_extractor.py`

### Project slug

```python
_PROJECT_SLUG = "restaurant-backend"
```

Same rationale as D.1: hardcoded because this extractor owns exactly one Sentry
project. The Orchestrator passes guardrails, not the project target.

### `run()` signature

```python
def run(guardrails: dict, issue_number: str = "") -> dict:
```

Identical to D.1. `issue_number` defaults to `""` so the Orchestrator can pass
it when wired up later without a breaking change today.

### Additional return fields

Backend errors carry HTTP context that frontend errors do not. D.2 adds two fields
to the `completed` return dict:

| Field | Type | Source | Notes |
|---|---|---|---|
| `endpoint` | `str` | `issue["culprit"]` | HTTP method + path, e.g. `"POST /api/reservations"` |
| `status_code` | `int` | `get_stack_trace()` response tags | HTTP status at time of error, e.g. `422` |

`endpoint` is already present in the trimmed issue dict returned by
`query_sentry_errors` as `culprit` — map it to `endpoint` in the result.
`status_code` must be extracted from the Sentry event response tags
(`data["tags"]` list, key `"status_code"`); default to `0` if absent.

### `get_status_code(event_data: dict) -> int`

A small private helper to extract `status_code` from the Sentry event tag list:

```python
def _get_status_code(event_data: dict) -> int:
    for tag in event_data.get("tags", []):
        if tag.get("key") == "status_code":
            return int(tag["value"])
    return 0
```

This keeps `get_stack_trace` reusable and untouched — `backend_sentry_extractor`
calls `get_stack_trace` for the stack, then separately calls
`_get_status_code(event_data)` on the same raw response.

**Note:** `get_stack_trace` in D.1 does not return `event_data` — D.2 must call
the Sentry `/events/latest/` endpoint directly (one extra HTTP call) to access
the raw tags. Do not modify `get_stack_trace` in D.1.

### Full `completed` return shape

```python
{
    "status": "completed",
    "source": "sentry-backend",
    "time_window": window,
    "pii_flag": _contains_pii(issue),
    "injection_flag": False,
    **issue,                     # id, title, level, culprit, count, ...
    **stack,                     # exception_type, exception_message, culprit, top_frames
    "releases": releases[:1],
    "endpoint": issue["culprit"],
    "status_code": _get_status_code(event_data),
}
```

### `no_data` and `injection_detected` shapes

Identical to D.1 — no `endpoint` or `status_code` on early-exit paths:

```python
# injection detected
{"status": "injection_detected", "source": "sentry-backend", "time_window": window}

# no issues found across all windows
{"status": "no_data", "source": "sentry-backend"}
```

### Observability

All 3 return paths must call `record_agent_run` before returning — same as D.1:

```python
record_agent_run("backend-sentry", result, usage_by_turn, issue_number)
```

---

## Acceptance Criteria

### Scenario 1 — Reservation failures (`reservation-validation-spike`)

Trigger: backend Sentry spike on `POST /api/reservations` with `TOO_LAST_MINUTE` errors.

The extractor must return a `completed` dict containing:

```python
{
    "status": "completed",
    "source": "sentry-backend",
    "endpoint": "POST /api/reservations",
    "status_code": 422,
    "exception_type": "HTTPValidationError",
    "exception_message": "Reservations must be made at least 2 hours in advance",
}
```

### Scenario 3 — Missing allergens (`missing-field-frontend-query`)

This is a frontend/GraphQL issue — no backend Sentry errors exist. The extractor
must return cleanly without raising:

```python
{"status": "no_data", "source": "sentry-backend"}
```

---

## TDD Test Plan

Write all tests in `agents/tests/test_backend_sentry_extractor.py`.
All tests must fail first, then be made green.

| # | Test name | What it asserts |
|---|---|---|
| 1 | `test_backend_sentry_returns_structured_findings_on_active_error` | `status=completed`, `source=sentry-backend`, `endpoint`, `status_code` present with correct values |
| 2 | `test_backend_sentry_escalates_window_when_first_window_empty` | `time_window=age:-6h` when first window returns nothing |
| 3 | `test_backend_sentry_returns_no_data_when_all_windows_empty` | `status=no_data`, `source=sentry-backend` |
| 4 | `test_backend_sentry_detects_injection_in_error_title` | `status=injection_detected` when title matches injection pattern |
| 5 | `test_backend_sentry_status_code_defaults_to_zero_when_tag_absent` | `status_code=0` when Sentry event has no `status_code` tag |

All tests must mock:
- `query_sentry_errors`
- `get_stack_trace`
- `get_affected_releases`
- `record_agent_run` — prevents real Sentry calls during tests

---

## Dependencies

All pulled from `agents/specs/DEPENDENCY_MAP.md`:

| Symbol | Source |
|---|---|
| `query_sentry_errors` | `agents/sentry_api.py` (moved from D.1 in Step 1) |
| `get_stack_trace` | `agents/sentry_api.py` |
| `get_affected_releases` | `agents/sentry_api.py` |
| `_pick_issue` | `agents/sentry_api.py` |
| `_looks_like_injection` | `agents/sentry_api.py` |
| `_contains_pii` | `agents/sentry_api.py` |
| `record_agent_run` | `agents/sentry_utils.py` |
| `SENTRY_WINDOW_LADDER`, `SENTRY_QUERY_LIMIT`, `SENTRY_STACK_FRAME_LIMIT` | `agents/config.py` |
