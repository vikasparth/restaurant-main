# D.5 — Codebase Agent Spec

**Status: DRAFT — awaiting sign-off**
**Architecture doc sections:** `Codebase Agent Query Contract`, `Agent Catalog`, `Principles`, `Codebase Agent Findings Schema`
**Dependency map:** `agents/specs/DEPENDENCY_MAP.md`

---

## What this slice builds

A Claude-assisted codebase navigator (`agents/codebase_agent.py`) that receives a crash location and list of changed files from the Orchestrator, then iteratively reads the filesystem to trace the root cause. Claude drives navigation — deciding what to read next — until the root cause is found or the turn budget is exhausted. Returns a structured findings dict (~50 tokens) to the Orchestrator. Zero interpretation, zero raw code snippets.

This is the first agent in the pipeline to make real Anthropic SDK calls. `usage_by_turn` is accumulated from every `client.messages.create()` call and passed to `record_agent_run`.

### Where This Agent Runs

Unlike D.1–D.4 (which call external HTTP APIs and can run anywhere), the Codebase Agent reads the local filesystem. It **must run on a GitHub Actions runner where the repository has been checked out**. File paths like `src/hooks/useMenu.ts` resolve relative to the repository root on the runner's local storage — they are physically present because of the `actions/checkout` step.

The only secret this agent requires is `ANTHROPIC_API_KEY`.

### Flow Diagram

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions Runner
    participant Orch as Orchestrator
    participant Agent as Codebase Agent
    participant FS as Local Filesystem<br/>(checked-out repo)
    participant Claude as Claude API<br/>(Anthropic SDK)

    GHA->>GHA: actions/checkout — repo on disk
    GHA->>Orch: trigger (Sentry alert + issue number)
    Orch->>Agent: run(guardrails) — crash_location, changed_files
    Agent->>Agent: _validate_guardrails()
    Agent->>Claude: messages.create() — system prompt + crash context

    loop Navigation (max CODEBASE_MAX_TURNS turns)
        Claude-->>Agent: tool_use: read_file(path)
        Agent->>FS: open(path) — injection check
        FS-->>Agent: file content
        Agent-->>Claude: tool_result: file content
        Claude-->>Agent: tool_use: list_directory(path) [optional]
        Agent->>FS: os.listdir(path)
        FS-->>Agent: filenames
        Agent-->>Claude: tool_result: filenames
    end

    Claude-->>Agent: tool_use: return_findings(findings dict)
    Agent->>Agent: capture findings, accumulate usage_by_turn
    Agent->>Agent: record_agent_run()
    Agent-->>Orch: structured findings dict
```

---

## Signature

```python
# agents/codebase_agent.py
def run(guardrails: dict, issue_number: str = "") -> dict:
    ...
```

**Guardrails consumed:**

| Key | Type | Source | Notes |
|---|---|---|---|
| `crash_location` | `str \| None` | Sentry extractor findings | File + line where error occurred, e.g. `src/components/MenuItemCard.tsx:42`. `None` for backend errors until task 3.14 (backend Sentry SDK) is complete |
| `endpoint` | `str \| None` | Render logs findings | Backend route that failed, e.g. `/api/menu`. Fallback navigation start when `crash_location` is `None` |
| `changed_files` | `list[str]` | GitHub extractor findings | Files changed in the release that triggered the error |
| `max_files_to_read` | `int` | Orchestrator guardrail | Hard cap on total files Claude may read in one run |

**Navigation start priority:** `crash_location` first (precise file + line); `endpoint` fallback when `crash_location` is `None`. Both `None` → return `no_data`.

---

## Return Shape

Matches `Codebase Agent Findings Schema` in `agent-architecture.md`.

```python
{
    "status": "completed",          # see Exit Conditions for full status set
    "source": "codebase",
    "crash_location":  "src/components/MenuItemCard.tsx:42",
    "root_cause_file": "src/hooks/useMenuItems.ts:23",
    "missing_field":   "price",                         # None if not a missing-field error
    "fix_location":    "graphql/menu.graphql — MenuItem type",
    "fix_type":        "add_field",                     # see Fix Types table below
    "fix_detail":      "Add price: Float! to MenuItem type and populate in useMenuItems hook",
    "runbook_match":   "missing-field-frontend-query",  # None if no match
    "injection_flag":  False,
    "pii_flag":        False,
}
```

**Fix Types:**

| Value | Meaning |
|---|---|
| `add_field` | A field is missing from a type, query, or schema |
| `remove_field` | A field was removed but is still referenced |
| `wrong_value` | A field exists but has an incorrect value or type |
| `missing_import` | A symbol is used but not imported |
| `logic_error` | Incorrect conditional, null check, or computation |
| `config_error` | A config value is missing or misconfigured |

Error statuses return a minimal dict:

```python
{"status": "<status>", "source": "codebase"}
```

---

## Implementation Rules

1. Import `CODEBASE_MODEL`, `CODEBASE_MAX_TURNS`, `CODEBASE_MAX_TOKENS` from `agents/config.py` — never hardcode.
2. Import `STATUS_COMPLETED`, `STATUS_NO_DATA`, `STATUS_INJECTION_DETECTED`, `STATUS_INVALID_INPUT`, `STATUS_PARTIAL` from `agents/config.py`. Add `STATUS_PARTIAL = "partial"` to `config.py` — it does not exist yet.
3. Import `_INJECTION_RE` from `agents/patterns.py` — used in `_read_file` to guard file content before returning it to Claude.
4. Import `record_agent_run` from `agents/sentry_utils.py` — call before every `return` in `run()`.
5. Import `build_system_prompt` from `agents/prompt_utils.py` — wrap the system prompt for prompt caching.
6. Use `anthropic.Anthropic()` client — do not instantiate inside the loop; create once before the loop.
7. Accumulate `usage_by_turn` after every `client.messages.create()` call — this agent makes real Claude API calls, unlike D.1–D.4.
8. The agentic loop is bounded by `CODEBASE_MAX_TURNS` — never use `while True`.
9. Claude returns findings via a `return_findings` tool call — do not parse free text. Capture the tool args dict as the result.
10. `_read_file` and `_list_directory` are the only filesystem access points — scope enforcement lives in these functions, not in the prompt.
11. No cross-feature imports — shared helpers come only from `patterns.py`, `sentry_utils.py`, `config.py`, `prompt_utils.py`.

---

## Filtering Pipeline

1. **Validate guardrails** — `max_files_to_read` must be a positive int; at least one of `crash_location` or `endpoint` must be a non-empty string. Return `invalid_input` immediately on failure — no Claude call made.
2. **Determine navigation start** — if `crash_location` is provided and in scope, use it. If `crash_location` is `None` or empty, fall back to `endpoint`. If both are absent, return `no_data`. Validate any provided `crash_location` starts with an allowed prefix (`src/`, `graphql-gateway/`, `backend/`, `docs/`).
3. **Build system prompt** — wrap with `build_system_prompt()` for prompt caching. System prompt instructs Claude: navigate read-only, call `return_findings` when done, never return raw code.
4. **Build initial user message** — pass `crash_location`, `changed_files`, and `max_files_to_read` as structured input.
5. **Agentic loop** — each turn: call `client.messages.create()`, append usage to `usage_by_turn`. On `stop_reason == "tool_use"`: dispatch to `_process_tool_call()`. On `stop_reason == "end_turn"` or `return_findings` tool called: exit loop.
6. **Injection guard in tool functions** — `_read_file` checks file content against `_INJECTION_RE` before returning it to Claude. On match: return injection error string to Claude and set `injection_flag = True`; `run()` returns `injection_detected` on next turn.
7. **Turn budget exhausted** — if loop exits without `return_findings` being called, return `status: partial` with whatever partial fields were extracted.

---

## Exit Conditions

| Status | Trigger | Orchestrator action |
|---|---|---|
| `completed` | Claude called `return_findings` with all required fields within turn budget | Pass to Recommendation Agent |
| `partial` | Turn budget (`CODEBASE_MAX_TURNS`) exhausted before `return_findings` called | Pass partial findings to Recommendation Agent with confidence penalty |
| `no_data` | `crash_location` not found in filesystem scope | Skip codebase findings in payload |
| `injection_detected` | `_INJECTION_RE` matched in file content during navigation | Flag on GitHub Issue; stop processing |
| `invalid_input` | Guardrails dict has wrong types or missing required fields | Log misconfiguration; skip codebase findings |

---

## Private Helper Functions

```python
def _validate_guardrails(guardrails: dict) -> str | None:
    # returns error string if both crash_location and endpoint are absent/empty, or max_files_to_read is not a positive int; None if valid

def _is_path_allowed(path: str) -> bool:
    # returns True if path starts with src/, graphql-gateway/, backend/, or docs/

def _read_file(path: str) -> str:
    # scope check via _is_path_allowed; injection check via _INJECTION_RE; returns file content or error string

def _list_directory(path: str) -> list[str]:
    # scope check via _is_path_allowed; returns sorted filenames or error string

def _build_tool_definitions() -> list[dict]:
    # returns Anthropic-format tool schemas for read_file, list_directory, and return_findings

def _process_tool_call(tool_name: str, tool_input: dict, files_read: list[str], max_files: int) -> tuple[str, bool]:
    # dispatches tool_name to the correct Python function; enforces max_files cap;
    # returns (result_string, injection_detected_flag)
```

---

## TDD Test Plan

File: `agents/tests/test_codebase_agent.py`

| # | Test name | Category | What it verifies |
|---|---|---|---|
| 1 | `test_returns_completed_when_claude_calls_return_findings` | Happy path | Claude calls `return_findings` → `status="completed"`, `source="codebase"`, all findings fields present |
| 2 | `test_returns_no_data_when_both_locations_absent` | Happy path | Both `crash_location` and `endpoint` absent → `status="no_data"`, no Claude call |
| 3 | `test_returns_partial_when_turn_budget_exhausted` | Happy path | SDK returns `tool_use` for all `CODEBASE_MAX_TURNS` turns without `return_findings` → `status="partial"` |
| 4 | `test_endpoint_fallback_used_when_crash_location_none` | Happy path | `crash_location=None`, `endpoint="/api/menu"` → Claude call made, `endpoint` passed as navigation start |
| 5 | `test_returns_invalid_input_when_both_locations_missing` | Input validation | `guardrails={}` → `status="invalid_input"`, no Claude call |
| 6 | `test_returns_invalid_input_when_max_files_not_int` | Input validation | `max_files_to_read="ten"` → `status="invalid_input"`, no Claude call |
| 7 | `test_returns_invalid_input_when_max_files_negative` | Input validation | `max_files_to_read=-1` → `status="invalid_input"`, no Claude call |
| 8 | `test_returns_no_data_when_crash_location_out_of_scope` | Input validation | `crash_location="etc/passwd"` → `status="no_data"`, no Claude call |
| 9 | `test_missing_api_key_returns_unauthenticated` | Authentication | `ANTHROPIC_API_KEY=""` → `status="unauthenticated"`, no SDK call made |
| 10 | `test_anthropic_401_returns_unauthenticated` | Authentication | SDK raises `anthropic.AuthenticationError` → `status="unauthenticated"` |
| 11 | `test_anthropic_400_returns_invalid_input` | Authentication | SDK raises `anthropic.BadRequestError` → `status="invalid_input"` (malformed tool definition or payload) |
| 12 | `test_anthropic_422_returns_invalid_input` | Authentication | SDK raises `anthropic.UnprocessableEntityError` → `status="invalid_input"` (payload rejected as semantically invalid) |
| 13 | `test_anthropic_403_returns_unauthorized` | Authorization | SDK raises `anthropic.PermissionDeniedError` → `status="unauthorized"` |
| 14 | `test_anthropic_404_returns_invalid_input` | Resource not found | SDK raises `anthropic.NotFoundError` → `status="invalid_input"` (model name in config doesn't exist) |
| 15 | `test_anthropic_429_returns_rate_limited` | Rate limiting | SDK raises `anthropic.RateLimitError` → `status="rate_limited"`, no retry inside agent |
| 16 | `test_anthropic_5xx_returns_server_error` | Server failures | SDK raises `anthropic.InternalServerError` → `status="server_error"` |
| 17 | `test_anthropic_409_returns_server_error` | Server failures | SDK raises `anthropic.ConflictError` → `status="server_error"` (treat as transient) |
| 18 | `test_anthropic_timeout_returns_timeout` | Network failures | SDK raises `anthropic.APITimeoutError` → `status="timeout"` |
| 19 | `test_anthropic_connection_error_returns_network_error` | Network failures | SDK raises `anthropic.APIConnectionError` → `status="network_error"` |
| 20 | `test_missing_stop_reason_returns_schema_error` | Schema validation | SDK response missing `stop_reason` → `status="schema_error"` |
| 21 | `test_missing_usage_returns_schema_error` | Schema validation | SDK response missing `usage` field → `status="schema_error"` |
| 22 | `test_injection_in_file_content_returns_injection_detected` | Filesystem | `_read_file` content matches `_INJECTION_RE` → `status="injection_detected"`, `injection_flag=True` |
| 23 | `test_read_file_blocked_outside_scope` | Filesystem | `_read_file("agents/config.py")` → returns error string, no file opened |
| 24 | `test_list_directory_blocked_outside_scope` | Filesystem | `_list_directory(".env")` → returns error string |
| 25 | `test_file_not_found_returns_error_string_to_claude` | Filesystem | `_read_file` on non-existent path → error string returned to Claude, loop continues |
| 26 | `test_max_files_cap_enforced` | Filesystem | `max_files_to_read=2`, Claude requests 3 reads → third call returns cap error string |
| 27 | `test_usage_by_turn_accumulated` | Observability | Two SDK turns → `record_agent_run` called with `usage_by_turn` of length 2 |
| 28 | `test_record_agent_run_called_on_every_return` | Observability | `record_agent_run` called for `completed`, `partial`, `invalid_input`, `no_data`, `unauthenticated` paths |
| 29 | `test_build_system_prompt_used` | Observability | `build_system_prompt` called — confirms caching wrapper always applied |
| 30 | `test_changed_files_included_in_initial_message` | Observability | `changed_files` from guardrails appears in first user message content |

All Claude SDK calls mocked with `unittest.mock.patch`. No real Anthropic API calls in tests.

---

## Files Touched

| File | Change |
|---|---|
| `agents/codebase_agent.py` | New — implementation |
| `agents/tests/test_codebase_agent.py` | New — 13 TDD tests |
| `agents/config.py` | Add `STATUS_PARTIAL = "partial"` |
| `agents/specs/DEPENDENCY_MAP.md` | Update — add `codebase_agent` row and tool definitions |

---

## Acceptance Criteria

- [ ] All 30 tests green
- [ ] Full test suite green (no regressions — currently 76 tests)
- [ ] No real Anthropic API calls in tests (all mocked)
- [ ] `record_agent_run` called on every return path
- [ ] `build_system_prompt` called — caching wrapper always applied
- [ ] `usage_by_turn` accumulated from every SDK call and passed to `record_agent_run`
- [ ] Filesystem scope enforced in tool functions, not in the prompt
- [ ] No hardcoded values — all config from `agents/config.py`
- [ ] No cross-feature imports
