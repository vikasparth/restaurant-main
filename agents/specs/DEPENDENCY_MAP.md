# Agents Dependency Map
**Read this before writing any new agents spec.**
For each new agent or tooling task, check which signatures already exist and reuse them.

---

## Quick Reference

| Task being written | Must pull signatures from |
|---|---|
| D.2 Backend Sentry Extractor | `sentry_api`: `query_sentry_errors`, `get_stack_trace`, `get_affected_releases`, `_pick_issue`, `_looks_like_injection`, `_contains_pii`; D.1 `run` pattern |
| D.3 Render Logs Extractor | D.1 `run` pattern; `sentry_utils.record_agent_run` |
| D.4 GitHub Extractor | D.1 `run` pattern; `sentry_utils.record_agent_run` | ✅ Done — see GitHub Extractor section below |
| D.5 Codebase Agent | D.1 `run` pattern; `prompt_utils.build_system_prompt`; `sentry_utils.record_agent_run` |
| D.6 Recommendation Agent | `prompt_utils.build_system_prompt`; `sentry_utils.record_agent_run`; all extractor `run` return shapes |
| E Orchestrator | All extractor `run` signatures; `validator.validate_finding`; `prompt_utils.build_system_prompt`; `sentry_utils.record_agent_run` |

---

## Shared Utilities (always check before writing new helpers)

| Function | Signature | File | Used by |
|---|---|---|---|
| `record_agent_run` | `record_agent_run(agent_name: str, result: dict, usage_by_turn: list[dict], issue_number: str = "") -> None` | `agents/sentry_utils.py` | All agents — call before every `return` in `run()` |
| `_INJECTION_RE` | `re.compile(...)` | `agents/patterns.py` | All extractors — use for injection detection; never redefine locally |
| `_EMAIL_RE` | `re.compile(...)` | `agents/patterns.py` | All extractors — use for PII email detection |
| `_PHONE_RE` | `re.compile(...)` | `agents/patterns.py` | All extractors — use for PII phone detection |
| `confidence_to_numeric` | `confidence_to_numeric(confidence: str) -> int` | `agents/sentry_utils.py` | Any agent that produces a confidence field; high→3, medium→2, low→1, unknown→0 |
| `build_system_prompt` | `build_system_prompt(text: str) -> list[dict]` | `agents/prompt_utils.py` | All Claude-calling agents (D.5, D.6, E) — wraps system prompt with `cache_control: ephemeral` |
| `validate_finding` | `validate_finding(yaml_str: str) -> dict` | `agents/validator.py` | Orchestrator — validates finding YAML against `agents/schemas/finding-schema.json` before routing |

---

## Sentry Shared Helpers (`agents/sentry_api.py` — import from here, not from extractor files)

| Function | Signature | Notes |
|---|---|---|
| `query_sentry_errors` | `query_sentry_errors(project_slug: str, window: str, limit: int) -> list[dict]` | Pass project slug per extractor. Returns trimmed issue fields only. |
| `get_stack_trace` | `get_stack_trace(issue_id: str, max_frames: int) -> dict` | Returns `exception_type`, `exception_message`, `culprit`, `top_frames` |
| `get_affected_releases` | `get_affected_releases(issue_id: str) -> list[str]` | Returns list of release version strings |
| `_pick_issue` | `_pick_issue(issues: list[dict]) -> dict` | Severity-first, then most recent `last_seen` |
| `_looks_like_injection` | `_looks_like_injection(issue: dict) -> bool` | Checks `title` + `culprit` against injection regex |
| `_contains_pii` | `_contains_pii(issue: dict) -> bool` | Checks `title` + `culprit` for email/phone patterns |

---

## Extractor `run()` Contract (D.1 — reference pattern for all pure Python extractors)

```python
def run(guardrails: dict, issue_number: str = "") -> dict:
    usage_by_turn = []          # empty for pure Python extractors — no Claude calls
    max_issues = guardrails.get("max_issues", SENTRY_QUERY_LIMIT)
    max_frames = guardrails.get("max_frames", SENTRY_STACK_FRAME_LIMIT)

    for window in SENTRY_WINDOW_LADDER:
        issues = query_sentry_errors(_PROJECT_SLUG, window, max_issues)
        if not issues:
            continue
        # ... pick, guard, extract ...
        record_agent_run("<agent-name>", result, usage_by_turn, issue_number)
        return result

    result = {"status": "no_data", "source": "<source-name>"}
    record_agent_run("<agent-name>", result, usage_by_turn, issue_number)
    return result
```

**Return dict — required fields for all extractors:**

| Field | Type | Notes |
|---|---|---|
| `status` | `str` | `"completed"`, `"no_data"`, `"partial"`, `"injection_detected"` |
| `source` | `str` | e.g. `"sentry-frontend"`, `"sentry-backend"` |
| `time_window` | `str` | The window that yielded results, e.g. `"age:-1h"` |
| `pii_flag` | `bool` | Result of `_contains_pii()` |
| `injection_flag` | `bool` | Always `False` on completed runs (injection returns early) |

**Backend Sentry extractor adds:**

| Field | Type | Notes |
|---|---|---|
| `endpoint` | `str` | HTTP path that triggered the error, e.g. `/api/reservations` |
| `http_status` | `int` | HTTP response status code at time of error |

---

## GitHub Extractor (`agents/github_extractor.py`)

| Function | Signature | Notes |
|---|---|---|
| `run` | `run(guardrails: dict, issue_number: str = "") -> dict` | Entry point — returns GitHub findings dict; all helpers are private |
| `_validate_guardrails` | `_validate_guardrails(guardrails: dict) -> str \| None` | Returns error string if invalid, `None` if valid; runs before any HTTP call |
| `_fetch_commits` | `_fetch_commits(anchor_sha: str, max_commits: int) -> list[dict]` | GET `/repos/{repo}/commits?sha={anchor}&per_page={n}`; raises on HTTP errors |
| `_fetch_changed_files` | `_fetch_changed_files(sha: str, max_files: int) -> list[str]` | GET `/repos/{repo}/commits/{sha}`; returns filenames only, capped at `max_files` |
| `_trim_commit` | `_trim_commit(raw: dict) -> dict` | Injection check (early return), PII flag, message trim, email dropped; returns `injection_flag` + `pii_flag` |

**Guardrails consumed:** `max_commits` (int, ≤ 100), `max_files_per_commit` (int, ≥ 0), `release_sha` (str | None)

**Return shape:** `status`, `source="github"`, `commit_window` (`branch`, `from_sha`, `to_sha`), `commit_count`, `commits[]`, `injection_flag`, `pii_flag`

---

## Config Constants (always import from `agents/config.py` — never hardcode)

| Constant | Type | Default | Purpose |
|---|---|---|---|
| `SENTRY_API_BASE` | `str` | `"https://sentry.io/api/0"` | Base URL for all Sentry API calls |
| `AGENTS_SENTRY_DSN` | `str` | `""` | Empty = opt-in; no-op locally without DSN |
| `SENTRY_WINDOW_LADDER` | `list[str]` | `["age:-1h","age:-6h","age:-24h"]` | Escalating windows for all Sentry extractors |
| `SENTRY_QUERY_LIMIT` | `int` | `3` | Max issues fetched per window |
| `SENTRY_STACK_FRAME_LIMIT` | `int` | `3` | Max app frames kept per stack trace |
| `ORCHESTRATOR_MODEL` | `str` | `claude-sonnet-4-6` | Model for Orchestrator Claude calls |
| `RECOMMENDATION_MODEL` | `str` | `claude-sonnet-4-6` | Model for Recommendation Agent |
| `CODEBASE_MODEL` | `str` | `claude-sonnet-4-6` | Model for Codebase Agent |
| `AGENT_MAX_TURNS` | `int` | `5` | Default turn budget for Claude-calling agents |
| `AGENT_MAX_TOKENS_PER_TURN` | `int` | `1024` | Default token budget per turn |
| `GITHUB_API_BASE` | `str` | `"https://api.github.com"` | Base URL for all GitHub API calls |
| `GITHUB_REPO` | `str` | `""` | `owner/repo` slug — set in `.env` |
| `GITHUB_TOKEN` | `str` | `""` | Personal access token — set in `.env` |
| `GITHUB_BRANCH` | `str` | `"main"` | Default branch used as HEAD anchor |
| `GITHUB_MAX_COMMITS` | `int` | `20` | Default commit fetch limit (≤ 100 GitHub platform cap) |
| `GITHUB_MSG_MAX_LEN` | `int` | `100` | Max chars kept from commit message first line |
| `GITHUB_MAX_FILES_PER_COMMIT` | `int` | `20` | Max filenames returned per commit |
