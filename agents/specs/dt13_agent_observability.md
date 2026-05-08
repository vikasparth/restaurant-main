# DT-13 Spec — Agent Observability via Sentry

**Status: Completed**
**Execution plan ref:** Developer Tooling → DT-13

---

## Goal

Every agent `run()` call is wrapped in a Sentry Performance transaction. Token usage
and confidence level are recorded as custom measurements. A Sentry dashboard shows
token spend and confidence trends per agent over time — without any custom scripts
or log files.

---

## What we are NOT building

- A custom log file or SQLite database
- A matplotlib script
- Any write operations to external systems from the agent loop

---

## New file — `agents/sentry_utils.py`

Single function: `record_agent_run(agent_name, result_yaml, usage_by_turn)`.

Called once at the end of every `run()` after the agentic loop completes.

**What it does:**
1. Initialises Sentry SDK (if `AGENTS_SENTRY_DSN` is set — skips silently if not, so local dev without DSN still works)
2. Creates a Sentry transaction named `agent.run` with tag `agent=<agent_name>`
3. Reads `status` and `confidence` from the result dict (`result.get("status")`, `result.get("confidence", "")`)
4. Sums `input_tokens`, `output_tokens`, `total_tokens` across all turns
5. Records tags: `agent`, `status`, `issue_number` (empty string if not provided — still queryable)
6. Records extra: `input_tokens`, `output_tokens`, `total_tokens`, `turns_used`, `confidence_numeric` (high=3, medium=2, low=1), `usage_by_turn` (raw list preserved for per-turn drill-down)
7. Calls `capture_event` — `issue_number` tag groups all agents from one investigation; `usage_by_turn` in extra shows token growth across turns for troubleshooting

**Signature:**
```python
def record_agent_run(
    agent_name: str,
    result: dict,              # structured dict returned by run(); not a YAML string
    usage_by_turn: list[dict], # each dict: {"input_tokens": int, "output_tokens": int}
    issue_number: str = "",    # GitHub Issue number — groups all agents from one investigation
) -> None
```

**Why `confidence_numeric`:** Sentry measurements are numeric — mapping high/medium/low
to 3/2/1 lets us plot average confidence per agent over time as a chart.

**Note on pure Python extractors:** Extractors that make no Claude calls (e.g. frontend-sentry,
backend-sentry) pass `usage_by_turn = []` so token sums are 0. They also have no `confidence`
key in their result dict — `confidence_numeric` will record 0 for these, which is correct
(0 means "not applicable", not "low confidence").

---

## Config changes — `agents/config.py`

Add one new constant:

```python
AGENTS_SENTRY_DSN = os.getenv("AGENTS_SENTRY_DSN", "")
```

Empty string default means observability is opt-in locally — agents run without it
until DSN is set. CI and production always have it set.

---

## `agents/.env.example` update

Add:
```
# --- Sentry (agent observability — Performance transactions) ---
# Create a new Sentry project: restaurant-agents
# Get DSN from: Sentry → restaurant-agents project → Settings → Client Keys
AGENTS_SENTRY_DSN=https://your-dsn@sentry.io/your-project-id
```

---

## `agents/requirements.txt` update

Add `sentry-sdk` pinned to exact version. After `pip install sentry-sdk`:
- Run `pip show sentry-sdk` and check `Requires:` field
- Pin all new transitive dependencies

---

## Agent changes — each `run()` function

Two changes per agent:

1. **Accumulate usage per turn** — append `{"input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens}` to a `usage_by_turn` list after each `client.messages.create()` call.

2. **Call `record_agent_run` before returning** — pass `agent_name`, the final YAML string, and `usage_by_turn`.

Applies to: `frontend_sentry_extractor.py` (D.1) + all future agents as they are built.

---

## Sentry project setup (manual step before code)

Create a new Sentry project `restaurant-agents` (Python platform).
Add `AGENTS_SENTRY_DSN` to `agents/.env`.
Add `AGENTS_SENTRY_DSN` to GitHub Actions secrets (for CI) and Render/production env.

---

## Sentry dashboard (manual step after first agent run)

Create a dashboard named `Agent Observability` with:

| Widget | Type | Query |
|---|---|---|
| Total tokens per agent | Bar chart | `transaction:agent.run` grouped by `agent` tag |
| Token trend over time | Line chart | `total_tokens` measurement over 30 days |
| Average confidence by agent | Bar chart | `confidence_numeric` measurement grouped by `agent` |
| Partial run rate | Table | `status:deadline_exceeded` count grouped by `agent` |

---

## TDD — `agents/tests/test_sentry_utils.py`

Tests must be written before implementation (red phase first):

1. `test_record_agent_run_completed` — mock `sentry_sdk`; pass a `{"status": "completed", "confidence": "high"}` dict, 2-turn usage, and `issue_number="47"`; assert `tags["agent"]`, `tags["status"]`, `tags["issue_number"]`, `extra["input_tokens"]`, `extra["output_tokens"]`, `extra["total_tokens"]`, `extra["turns_used"]`, `extra["confidence_numeric"]`, and `extra["usage_by_turn"]` (full list preserved)
2. `test_record_agent_run_partial` — pass a `{"status": "partial", "confidence": "low"}` dict; assert `tags["status"] == "partial"` and `extra["confidence_numeric"] == 1`
3. `test_record_agent_run_no_dsn` — `AGENTS_SENTRY_DSN` not set; assert function returns without calling `sentry_sdk.init` (observability is opt-in)
4. `test_confidence_numeric_mapping` — high=3, medium=2, low=1, missing=0
5. `test_record_agent_run_issue_number_tag` — pass `issue_number="123"`; assert `event["tags"]["issue_number"] == "123"`
6. `test_record_agent_run_usage_by_turn_preserved` — pass 3-turn usage list; assert `event["extra"]["usage_by_turn"]` equals the exact input list (not summed)

---

## Open questions for sign-off

1. **Sentry project:** Use a new `restaurant-agents` project (clean separation) or reuse the existing `restaurant-backend` project (simpler setup)? Recommendation: new project — same reason as per-project env ownership.
2. **`sentry-release`:** Should agent transactions be tagged with the Git SHA? Adds correlation between a deploy and a confidence drop. Requires `GIT_COMMIT_SHA` env var already set on Render.

---

## Post-implementation Findings (2026-05-03)

### Sentry Performance not available on free plan
`start_transaction()` sent events but they did not appear in the Performance tab.
Sentry confirmed Performance requires a paid plan for full visibility.
**Decision:** `capture_event()` used instead — works on all plans, lands in Issues/Events,
fully queryable in dashboards via tags and extras.
**Status: Done (2026-05-05)**

---

## Sequence of work

1. ✅ Answer open questions above
2. ✅ Create `restaurant-agents` Sentry project, add DSN to `agents/.env`
3. ✅ Write failing tests (`test_sentry_utils.py`) — red phase
4. ✅ Implement `agents/sentry_utils.py` — green phase
5. ✅ Update `agents/config.py`
6. ✅ Update `agents/requirements.txt`
7. ✅ Update `agents/.env.example`
8. ✅ Wire `record_agent_run` into `frontend_sentry_extractor.py`
9. ✅ Update `record_agent_run` signature to `result: dict` — YAML parsing and `_strip_code_fence` removed (done 2026-05-05 as part of DT-15)
10. ✅ Switch to `capture_event()` — free-plan compatible (done 2026-05-05)
11. ⬜ Add `issue_number: str = ""` param — tag groups all agents from one investigation in Sentry
12. ⬜ Add `usage_by_turn` list to `extra` — preserves per-turn token data for troubleshooting token growth across turns
13. ⬜ Update `test_sentry_utils.py` — assert `issue_number` tag and `usage_by_turn` in extra (tests 5 and 6 above)
14. ⬜ Wire `issue_number` into Orchestrator → passed to each agent's `run()` → forwarded to `record_agent_run` (E.2)
15. ⬜ Build Sentry dashboard — filter by `issue_number` to see all agents per investigation; `usage_by_turn` visible in event detail
