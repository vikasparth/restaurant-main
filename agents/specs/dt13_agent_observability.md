# DT-13 Spec — Agent Observability via Sentry

**Status: Awaiting sign-off**
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
3. Parses `confidence` and `status` from the returned YAML
4. Sums `input_tokens`, `output_tokens`, `total_tokens` across all turns
5. Records measurements: `input_tokens`, `output_tokens`, `total_tokens`, `turns_used`, `confidence_numeric` (high=3, medium=2, low=1)
6. Sets transaction status: `ok` for `completed`, `deadline_exceeded` for `partial`
7. Finishes the transaction

**Signature:**
```python
def record_agent_run(
    agent_name: str,
    result_yaml: str,
    usage_by_turn: list[dict],  # each dict: {"input_tokens": int, "output_tokens": int}
) -> None
```

**Why `confidence_numeric`:** Sentry measurements are numeric — mapping high/medium/low
to 3/2/1 lets us plot average confidence per agent over time as a chart.

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

Applies to: `frontend_sentry_agent.py` (D.1) + all future agents as they are built.

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

1. `test_record_agent_run_completed` — mock `sentry_sdk`; pass a `completed`/`high` YAML and 2-turn usage; assert transaction name, tag, measurements, and `ok` status were set
2. `test_record_agent_run_partial` — pass a `partial` YAML; assert `deadline_exceeded` status
3. `test_record_agent_run_no_dsn` — `AGENTS_SENTRY_DSN` not set; assert function returns without calling `sentry_sdk.init` (observability is opt-in)
4. `test_confidence_numeric_mapping` — high=3, medium=2, low=1, missing=0

---

## Open questions for sign-off

1. **Sentry project:** Use a new `restaurant-agents` project (clean separation) or reuse the existing `restaurant-backend` project (simpler setup)? Recommendation: new project — same reason as per-project env ownership.
2. **`sentry-release`:** Should agent transactions be tagged with the Git SHA? Adds correlation between a deploy and a confidence drop. Requires `GIT_COMMIT_SHA` env var already set on Render.

---

## Sequence of work

1. Answer open questions above
2. Create `restaurant-agents` Sentry project, add DSN to `agents/.env`
3. Write failing tests (`test_sentry_utils.py`) — red phase
4. Implement `agents/sentry_utils.py` — green phase
5. Update `agents/config.py`
6. Update `agents/requirements.txt`
7. Update `agents/.env.example`
8. Wire `record_agent_run` into `frontend_sentry_agent.py` + verify transaction appears in Sentry
9. Build Sentry dashboard
10. Commit + PR
