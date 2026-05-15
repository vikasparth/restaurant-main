# Spec Profile — Agents Layer

This profile is loaded by the `/spec` skill when the layer is `agents`.
It defines everything specific to writing a spec for an agent extractor.

---

## Profile Config

```
dependency_map:   agents/specs/DEPENDENCY_MAP.md
spec_output_dir:  agents/specs/
spec_filename:    d{task_id}_{slug}.md          # e.g. d5_codebase_extractor.md
test_skills:
  - api-integration-tests                       # every extractor calls an external HTTP API
```

---

## Always Read Architecture Sections

In addition to the sections in the task's `Arch sections:` field, always read:

- `Agent Catalog` — confirms the extractor's role and its position in the pipeline
- `Principles` — token efficiency, trim-at-boundary, PII rules, injection guards

---

## Agent-Layer Invariants

These rules apply to every agent extractor spec regardless of task. Do not omit or soften them.

**Signature — fixed contract:**
```python
def run(guardrails: dict, issue_number: str = "") -> dict:
```
All extractors use this exact signature. `issue_number` defaults to `""` — the
Orchestrator can pass it without a breaking change.

**Observability — mandatory:**
- `usage_by_turn = []` must be initialised before any loop
- `record_agent_run()` must be called before **every** `return` — no exceptions
- Pure Python extractors make zero Claude API calls — `usage_by_turn` stays empty

**Status constants — reuse, never redefine:**
Import from `agents/config.py`. Check the dependency map before adding any new STATUS_
constant. If the status you need already exists, import it. If it is genuinely new, add it
to `agents/config.py` first and document it in the spec.

**PII and injection — mandatory pipeline steps:**
Every extractor that reads external API responses must include:
- Injection check: test against `_INJECTION_RE` from `agents/patterns.py`; return `injection_detected` immediately on match
- PII check: test against `_EMAIL_RE` and `_PHONE_RE` from `agents/patterns.py`; strip match and set `pii_flag=True`; do not return early

**Imports — no cross-feature imports:**
All shared helpers come from `agents/patterns.py`, `agents/sentry_utils.py`, or `agents/config.py`.
Never import from another extractor file.

---

## Spec Template

Generate the spec with exactly these sections in this order.

```
# {Task ID} — {Extractor Name} Spec

**Status: DRAFT — awaiting sign-off**
**Architecture doc sections:** {list sections read in Steps 3}
**Dependency map:** agents/specs/DEPENDENCY_MAP.md

---

## What this slice builds

{One paragraph: what the extractor does, what API it calls, what it returns to the
Orchestrator. State explicitly: "Zero Claude API calls."}

---

## Signature

```python
# agents/{name}_extractor.py
def run(guardrails: dict, issue_number: str = "") -> dict:
    ...
```

**Guardrails consumed:**

| Key | Type | Source | Notes |
|---|---|---|---|
{one row per guardrail key the Orchestrator passes}

---

## Return Shape

Matches the `{Finding Schema section name}` in the architecture doc.

```python
{
    "status": "completed",        # see Exit Conditions for full status set
    "source": "{source-name}",
    ...                           # all fields the Orchestrator and Recommendation Agent read
    "injection_flag": False,
    "pii_flag": False,
}
```

Error statuses return a minimal dict:
```python
{"status": "<status>", "source": "{source-name}"}
```

---

## Implementation Rules

1. Import all config constants from `agents/config.py` — never hardcode URLs, limits, or keys.
2. Import `_INJECTION_RE`, `_EMAIL_RE`, `_PHONE_RE` from `agents/patterns.py`.
3. Import `record_agent_run` from `agents/sentry_utils.py` — call before every `return`.
4. Use STATUS_ constants from `agents/config.py` — never use raw strings.
5. `usage_by_turn = []` — pure Python extractor, no Claude calls, list stays empty.
{add extractor-specific rules here, numbered from 6 onward}

---

## Filtering Pipeline (ordered)

1. **Validate guardrails** — type and range checks before any HTTP call; return `invalid_input` on failure.
2. **Check credentials** — if the API token/key is empty, return `unauthenticated` immediately. No HTTP call.
{add extractor-specific pipeline steps here, numbered from 3 onward}
N-1. **Injection check** — test each text field against `_INJECTION_RE`; return `injection_detected` on match.
N.   **PII check** — test each text field against `_EMAIL_RE` and `_PHONE_RE`; strip match, set `pii_flag=True`.

---

## Exit Conditions

| Status | Trigger | Orchestrator action |
|---|---|---|
| `completed` | At least one result found | Pass to Recommendation Agent |
| `no_data` | Zero results after filtering | Skip this source in payload |
| `injection_detected` | Injection pattern matched | Flag on GitHub Issue; stop processing |
| `invalid_input` | Guardrails have wrong types or values | Log misconfiguration; skip this source |
| `unauthenticated` | Token empty or API returns 401 | Alert owner — token missing or expired |
| `unauthorized` | API returns 403 | Alert owner — token lacks required scope |
| `not_found` | API returns 404 | Alert owner — wrong config value |
| `rate_limited` | API returns 429 | Back off; retry at next scheduled run |
| `server_error` | API returns 5xx | Treat as transient; retry at next run |
| `timeout` | requests.Timeout raised | Treat as transient; retry at next run |
| `network_error` | requests.ConnectionError raised | Treat as transient; retry at next run |
| `schema_error` | Response missing expected fields | Log unexpected shape; skip this source |

---

## Private Helper Functions

```python
def _validate_guardrails(guardrails: dict) -> str | None:
    # returns error message string if invalid, None if valid
    ...

{add one stub per private helper, with a one-line comment describing its contract}
```

---

## TDD Test Plan

File: `agents/tests/test_{name}_extractor.py`

| # | Test name | Category | What it verifies |
|---|---|---|---|
{generated by /api-integration-tests skill — filled in at Step 7}

All HTTP calls mocked with `unittest.mock.patch`. No real API calls in tests.

---

## Files Touched

| File | Change |
|---|---|
| `agents/{name}_extractor.py` | New — implementation |
| `agents/tests/test_{name}_extractor.py` | New — TDD tests |
| `agents/specs/DEPENDENCY_MAP.md` | Update — add new extractor row and any new config constants |
| `agents/config.py` | Update — add any new config constants (if needed) |
| `agents/.env.example` | Update — add any new env var entries (if needed) |

---

## Acceptance Criteria

- [ ] All {N} tests green
- [ ] Full test suite green (no regressions — currently {current_count} tests)
- [ ] No real API calls in tests (all mocked)
- [ ] `record_agent_run` called on every return path
- [ ] Guardrail validation runs before any HTTP call
- [ ] No hardcoded values — all config from `agents/config.py`
- [ ] No cross-feature imports — all shared helpers from `patterns.py`, `sentry_utils.py`, `config.py`
- [ ] `agents/specs/DEPENDENCY_MAP.md` updated with new slice's signatures
```
