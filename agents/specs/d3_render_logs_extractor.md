# D.3 Spec — Render Logs Extractor

**Status: Awaiting sign-off**
**Execution plan ref:** D.3 — Render Logs Extractor
**Architecture doc sections:** `Render Agent Query Contract`, `Render Logs Findings Schema`, `Principles`

---

## Goal

A pure Python extractor that queries the Render REST API for backend service log lines,
filters to `error` and `warn` level, deduplicates by message text, and returns a
structured dict the Orchestrator can route downstream.

Zero Claude API calls — `usage_by_turn` is always an empty list.

---

## What we are NOT building

- No Claude API calls — `usage_by_turn = []` always empty
- No window ladder — Render uses a single time window from guardrails (not an escalating
  ladder like the Sentry extractors)
- No new config constants — all Render constants were added in A.6:
  `RENDER_API_BASE`, `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_LOG_FETCH_LIMIT`,
  `RENDER_MAX_DISTINCT_ERRORS`, `RENDER_LOG_MAX_MSG_LEN`

---

## New file: `agents/render_logs_extractor.py`

### `run()` signature

```python
def run(guardrails: dict, issue_number: str = "") -> dict:
```

`issue_number` defaults to `""` so the Orchestrator can pass it later without a
breaking change today.

### Time window

The guardrail `time_window` is an integer number of hours (default `1`). The extractor
converts it to ISO 8601 UTC timestamps and passes them as `startTime` / `endTime`
query parameters:

```
end_time   = now (UTC)
start_time = end_time minus time_window hours
```

The `log_window` field in the return dict records these two timestamps so the
Orchestrator knows exactly what period was sampled.

### Filtering pipeline

Applied in Python before returning anything — always in this order:

1. **Drop `deploy` lines** — keep only lines where `type == "app"`.
2. **Parse JSON messages** — if a `message` value is valid JSON, promote known fields
   to top-level keys on that entry: `event`, `status`, `duration_ms`, `path`,
   `request_id`.
3. **Filter by level** — keep `error` and `warn` only. Level is read from a `level`
   field if present; otherwise inferred from the message text (`ERROR`, `WARN`,
   `WARNING` keywords) or an HTTP 5xx `status` value.
4. **Injection check** — if any message matches the injection pattern (e.g.
   "ignore previous instructions"), return `injection_detected` immediately.
   Never pass injected content further.
5. **PII check** — if any message matches an email or phone pattern, set
   `pii_flag = True` and strip the matching field value before continuing.
6. **Deduplicate** — group lines with identical `message` text; count occurrences;
   record the earliest and latest timestamps as `first_at` / `last_at`. If a
   plain-text message exceeds `RENDER_LOG_MAX_MSG_LEN` characters, truncate it and
   set `truncated: True` on that entry.
7. **Cap** — if more than `RENDER_MAX_DISTINCT_ERRORS` distinct errors remain, keep
   only the entries with the highest occurrence counts.

### Return shapes

**`completed`** — at least one error/warn line was found after filtering:

```python
{
    "status": "completed",
    "source": "render-api",
    "log_window": {
        "from": "2026-05-11T09:00:00Z",
        "to":   "2026-05-11T10:00:00Z",
    },
    "error_count": 47,          # total occurrences across all distinct errors
    "errors": [
        {
            "level":       "error",
            "count":       40,
            "event":       "cold_start",
            "path":        "/api/reservations",
            "status":      503,   # HTTP status code inside the log entry (not extractor status)
            "duration_ms": 8420,
            "message":     "Service starting",
            "first_at":    "2026-05-11T09:14:22Z",
            "last_at":     "2026-05-11T09:58:00Z",
            "request_id":  "abc123",
            "truncated":   False,
        }
    ],
    "injection_flag": False,
    "pii_flag": False,
}
```

**`no_data`** — zero error/warn lines in the requested time window:

```python
{"status": "no_data", "source": "render-api"}
```

**`injection_detected`** — injection pattern matched in any log line:

```python
{"status": "injection_detected", "source": "render-api"}
```

### Observability

All three return paths must call `record_agent_run` before returning:

```python
record_agent_run("render-logs", result, usage_by_turn, issue_number)
```

---

## Acceptance Criteria

### Scenario 2 — Cold start (`cold-start-reservations`)

Trigger: Render service restarting under load; `POST /api/reservations` returns 503s.

The extractor must return a `completed` dict that includes:

```python
{
    "status": "completed",
    "source": "render-api",
    "errors": [
        {
            "level":  "error",
            "event":  "cold_start",
            "path":   "/api/reservations",
            "status": 503,
        }
    ],
}
```

### No backend errors

No error or warn level log lines in the time window. The extractor must return cleanly
without raising:

```python
{"status": "no_data", "source": "render-api"}
```

---

## TDD Test Plan

Write all tests in `agents/tests/test_render_logs_extractor.py`.
All tests must fail first, then be made green.

| # | Test name | What it asserts |
|---|---|---|
| 1 | `test_render_logs_returns_completed_on_error_lines` | `status=completed`, `source=render-api`, errors list present with correct fields |
| 2 | `test_render_logs_returns_no_data_when_no_error_warn_lines` | `status=no_data` when all lines are `info` or `debug` |
| 3 | `test_render_logs_drops_deploy_type_lines` | `status=no_data` when all lines have `type=deploy`, even if level is `error` |
| 4 | `test_render_logs_injection_detected_halts_immediately` | `status=injection_detected` when any line contains injection pattern |
| 5 | `test_render_logs_deduplicates_identical_messages` | two lines with identical message collapsed into one entry with `count=2` |
| 6 | `test_render_logs_caps_at_max_distinct_errors` | only `RENDER_MAX_DISTINCT_ERRORS` entries returned; highest occurrence counts kept |

All tests must mock:
- `requests.get` (or equivalent HTTP call) — prevents real Render API calls during tests
- `record_agent_run` — prevents real Sentry calls during tests

---

## Dependencies

All pulled from `agents/specs/DEPENDENCY_MAP.md`:

| Symbol | Source |
|---|---|
| `record_agent_run` | `agents/sentry_utils.py` |
| `_INJECTION_RE` | `agents/patterns.py` |
| `RENDER_API_BASE` | `agents/config.py` |
| `RENDER_SERVICE_ID` | `agents/config.py` |
| `RENDER_API_KEY` | `agents/config.py` |
| `RENDER_LOG_FETCH_LIMIT` | `agents/config.py` |
| `RENDER_MAX_DISTINCT_ERRORS` | `agents/config.py` |
| `RENDER_LOG_MAX_MSG_LEN` | `agents/config.py` |

## Post-slice: update DEPENDENCY_MAP

After D.3 is complete, add the following row to the `agents/specs/DEPENDENCY_MAP.md`
quick-reference table:

```
| D.4 GitHub Extractor | D.1 `run` pattern; `sentry_utils.record_agent_run`; D.3 return shape as reference |
```

And add `render_logs_extractor.run` to the extractor signatures section so D.6 and E
can find it.
