# D.6 — Coding Agent Spec

**Architecture doc sections:** `Coding Agent`, `Agent Catalog`, `Principles`,
`Confidence-Gated Actions`, `Human in the Loop`, `Runbook Integration`,
`Compliance Awareness`, `Token Budget Targets`

---

## 1. What This Slice Builds

The Coding Agent is the only agent in the pipeline that produces interpretation.
It receives the combined structured payload assembled by the Orchestrator (all extractor
findings clubbed into one dict) and makes a **single Claude API call** to produce a
cross-source root cause analysis. After Claude responds, Python code opens a draft GitHub
PR on a new feature branch if confidence is `high` or `medium`. Low-confidence findings
skip the PR and return a comment-only result.

The agent returns a dict containing `interpretation` (root cause, affected layer,
regression flag, confidence, recommended fix, runbook reference) plus `pr_url` (the
draft PR link, or `None` if skipped or failed). Both are returned to the Orchestrator so
it can notify the human in a single message.

**This agent makes zero filesystem reads and has no access to Sentry, Render, or the
local codebase.** Its only external calls are one Anthropic SDK call and, conditionally,
two GitHub API calls (create branch + open draft PR).

---

## 2. Signature

```python
def run(payload: dict, issue_number: str = "") -> dict:
    ...
```

**`payload`** — the combined findings dict assembled by the Orchestrator. Contains one
or more source blocks (keys: `sentry_frontend`, `sentry_backend`, `render_logs`,
`github`, `codebase`) plus a top-level `pii_flag` and `injection_flag` merged across
sources.

**`issue_number`** — GitHub issue number as a string (e.g. `"42"`); used as the suffix
in the PR branch name `fix/sentry-{issue_number}` and passed to `record_agent_run`.
Empty string when called outside a GitHub issue context.

---

## 3. Guardrails Consumed

| Guardrail | Source | Type | Notes |
|---|---|---|---|
| `CODING_MAX_TURNS` | `agents/config.py` | `int` (= 1) | Bounds the single Claude call; not a loop limit |
| `CODING_MAX_TOKENS` | `agents/config.py` | `int` | Max output tokens per Claude response |
| `CODING_MODEL` | `agents/config.py` | `str` | Sonnet 4.6 — strongest reasoning needed for cross-source synthesis |
| `GITHUB_API_BASE` | `agents/config.py` | `str` | Base URL for all GitHub API calls |
| `GITHUB_REPO` | `agents/config.py` | `str` | `owner/repo` slug |
| `GITHUB_TOKEN` | `agents/config.py` | `str` | Personal access token — write scope required |
| `GITHUB_BRANCH` | `agents/config.py` | `str` | Base branch for PR (default `"main"`) |
| `GITHUB_PR_BRANCH_PREFIX` | `agents/config.py` | `str` | New constant — branch name prefix (default `"fix/sentry-"`) |

> **New constant required:** `GITHUB_PR_BRANCH_PREFIX = os.getenv("GITHUB_PR_BRANCH_PREFIX", "fix/sentry-")` in `agents/config.py`.

---

## 4. Return Shape

```python
{
    "status":         str,   # STATUS_COMPLETED | STATUS_NO_DATA | STATUS_PARTIAL
                             # | STATUS_INVALID_INPUT | STATUS_INJECTION_DETECTED
                             # | STATUS_UNAUTHENTICATED | STATUS_UNAUTHORIZED
                             # | STATUS_RATE_LIMITED | STATUS_SERVER_ERROR
                             # | STATUS_NETWORK_ERROR | STATUS_SCHEMA_ERROR
    "source":         "recommendation",
    "interpretation": {      # present only when status == STATUS_COMPLETED
        "root_cause":       str,   # cross-source narrative, ~50-100 words
        "affected_layer":   str,   # "frontend" | "backend" | "graphql" | "database" | "unknown"
        "regression":       bool,  # True if first_seen is after pr_merged_at
        "confidence":       str,   # "high" | "medium" | "low"
        "recommended_fix":  str,   # actionable one-sentence fix directive
        "runbook_match":    str | None,  # matched pattern name or None
    },
    "pr_url":         str | None,  # draft PR HTML URL; None if low confidence or PR failed
    "pii_flag":       bool,        # inherited from payload's merged pii_flag
    "injection_flag": bool,        # inherited from payload's merged injection_flag
}
```

**`STATUS_PARTIAL`** — Claude returned a valid interpretation but the GitHub PR creation
failed (branch or PR API error). Interpretation is still returned; `pr_url` is `None`.

---

## 5. Implementation Rules

1. **Single Claude call only.** `CODING_MAX_TURNS` is 1. There is no loop.
   Call `client.messages.create()` exactly once per `run()` invocation.

2. **Use `build_system_prompt()`** from `agents/prompt_utils.py` to wrap the system
   prompt with `cache_control: ephemeral`. The system prompt does not change between
   runs — every cache hit costs ~90% less on input tokens.

3. **Force structured output via `return_interpretation` tool.** Register a single tool
   definition (see `_build_tool_definitions()`). Pass `tool_choice={"type": "any"}` so
   Claude must call the tool. Parse the `tool_use` block to get the interpretation dict.
   If no `tool_use` block is present in the response, return `STATUS_SCHEMA_ERROR`.

4. **Troubleshooting sequence — prompt must instruct Claude in this order:**
   1. Regression check — compare `first_seen` vs `pr_merged_at` across GitHub and Sentry findings
   2. File overlap check — compare `top_frames` file paths vs `files_changed` in GitHub commits
   3. Severity check — weight `user_count` and `error_count` from Sentry
   4. Fix derivation — use `fix_location`, `fix_type`, `fix_detail` from Diagnostic Agent only
   5. Confidence scoring — combine regression flag + file overlap + severity + fix clarity

5. **Confidence-gated PR:**
   - `high` or `medium` → call `_open_draft_pr()` after Claude responds
   - `low` → set `pr_url = None`, do not call GitHub API at all

6. **PR branch pattern:** `{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{YYYYMMDDHHMMSS}` (e.g.
   `fix/sentry-42-20260519143022`). The timestamp suffix is generated at call time using
   `datetime.utcnow().strftime("%Y%m%d%H%M%S")`. This guarantees uniqueness across
   re-runs and eliminates the 422 "ref already exists" collision. The branch is created
   from the HEAD SHA of `GITHUB_BRANCH`.

7. **`record_agent_run()` before every `return`.** Pass `usage_by_turn` (one entry from
   the single Claude call), the result dict, and `issue_number`.

8. **`confidence_to_numeric()`** — call before `record_agent_run()` to log confidence
   numerically; do not compute it locally.

9. **PII and injection flags** — inherit the merged flags from the incoming `payload`.
   Do not re-scan the payload — the Orchestrator has already checked each extractor's
   flags. If `payload.injection_flag` is `True`, return `STATUS_INJECTION_DETECTED`
   immediately without calling Claude.

10. **All constants from `agents/config.py`** — no model names, URLs, branch prefixes,
    or token limits hardcoded in `coding_agent.py`.

11. **No cross-feature imports.** Import only from `agents/prompt_utils.py`,
    `agents/sentry_utils.py`, and `agents/config.py`.

---

## 6. Filtering Pipeline

Not applicable — this agent receives an already-trimmed combined payload from the
Orchestrator. No additional trimming is performed here.

---

## 7. Exit Conditions

| Status | Trigger | What is returned |
|---|---|---|
| `STATUS_COMPLETED` | Claude returns valid `return_interpretation` tool call; PR created (or skipped for low confidence) | Full dict with `interpretation` and `pr_url` |
| `STATUS_PARTIAL` | Claude returned valid interpretation but GitHub PR creation failed | `interpretation` present; `pr_url` is `None` |
| `STATUS_NO_DATA` | `payload` is empty or all source statuses are `no_data` | `{"status": "no_data", "source": "recommendation"}` |
| `STATUS_INVALID_INPUT` | `_validate_payload()` returns an error string | `{"status": "invalid_input", "source": "recommendation", "error": <msg>}` |
| `STATUS_INJECTION_DETECTED` | `payload.get("injection_flag")` is `True` | `{"status": "injection_detected", "source": "recommendation"}` |
| `STATUS_UNAUTHENTICATED` | `APIStatusError` 401 from Anthropic, or `GITHUB_TOKEN` empty on PR path | Status dict with source |
| `STATUS_UNAUTHORIZED` | `APIStatusError` 403 from Anthropic or GitHub | Status dict with source |
| `STATUS_RATE_LIMITED` | `APIStatusError` 429 from Anthropic | Status dict with source |
| `STATUS_SERVER_ERROR` | `APIStatusError` 5xx from Anthropic or GitHub | Status dict with source |
| `STATUS_NETWORK_ERROR` | `APIConnectionError` or `requests.exceptions.ConnectionError` | Status dict with source |
| `STATUS_SCHEMA_ERROR` | Claude response contains no `tool_use` block, or `return_interpretation` input fails schema check | Status dict with source |

---

## 8. Private Helper Functions

```python
def _validate_payload(payload: dict) -> str | None:
    # Returns an error string if payload is empty, missing required top-level keys,
    # or if every source has status "no_data" or "failed".
    # Returns None if the payload is usable.

def _build_tool_definitions() -> list[dict]:
    # Returns the Anthropic tool schema list containing one tool: "return_interpretation".
    # The tool's input_schema enforces all interpretation fields:
    #   root_cause (string), affected_layer (enum), regression (bool),
    #   confidence (enum: high|medium|low), recommended_fix (string),
    #   runbook_match (string or null).

def _parse_interpretation(response) -> dict | None:
    # Finds the first tool_use block in response.content where name=="return_interpretation".
    # Returns the block's "input" dict, or None if not found.

def _should_open_pr(confidence: str) -> bool:
    # Returns True only for "high" or "medium" confidence.
    # Low confidence finding does not warrant a draft PR.

def _format_pr_body(interpretation: dict, payload: dict) -> str:
    # Builds the markdown PR description from interpretation + key payload fields.
    # Includes: root cause summary, affected layer, confidence, recommended fix,
    # evidence summary (which sources contributed), and link to GitHub issue.
    # Never includes raw code snippets, PII, or injection-flagged content.

def _open_draft_pr(interpretation: dict, payload: dict, issue_number: str) -> str | None:
    # Orchestrates: get base SHA → create branch → open draft PR.
    # Branch name: f"{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}".
    # Timestamp suffix guarantees uniqueness — no 422 "ref already exists" collision on re-runs.
    # Uses GITHUB_API_BASE, GITHUB_REPO, GITHUB_TOKEN from config.
    # Returns the draft PR's html_url on success, None on any HTTP or network error.
    # Logs the failure reason but does not raise — caller downgrades to STATUS_PARTIAL.
```

---

## 9. TDD Test Plan

**Integrations under test:**
- Anthropic Claude API (SDK) — single `client.messages.create()` call, `return_interpretation` tool
- GitHub API (requests + Bearer token) — `GET /branches/{branch}`, `POST /git/refs`, `POST /pulls`

**Category 7c (multi-turn loop invariants):** Not applicable — single-call agent, no loop.
**Category 9 (pagination):** Not applicable — no paginated responses.

| # | Test name | Category | What it verifies |
|---|---|---|---|
| 1 | `test_high_confidence_payload_returns_completed_and_pr_url` | 1 — Happy Path | Valid payload, Claude returns high confidence, GitHub creates PR → `status=completed`, `pr_url` populated, all interpretation fields present |
| 2 | `test_medium_confidence_payload_returns_completed_and_pr_url` | 1 — Happy Path | Medium confidence → `status=completed`, `pr_url` populated, `_open_draft_pr` called |
| 3 | `test_low_confidence_payload_returns_completed_without_pr` | 1 — Happy Path | Low confidence → `status=completed`, `pr_url=None`, `_open_draft_pr` never called |
| 4 | `test_pr_branch_name_includes_unique_timestamp_suffix` | 1 — Happy Path | Branch name passed to GitHub matches `{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{14-digit-timestamp}` — assert starts with prefix and ends with timestamp pattern |
| 5 | `test_none_payload_returns_invalid_input_without_api_call` | 2 — Input Validation | `None` passed as payload → `invalid_input`, no HTTP call made |
| 6 | `test_empty_dict_payload_returns_invalid_input_without_api_call` | 2 — Input Validation | `{}` passed → `invalid_input`, no HTTP call made |
| 7 | `test_all_sources_no_data_returns_no_data_without_api_call` | 2 — Input Validation | Every source in payload has `status=no_data` → `no_data`, no HTTP call made |
| 8 | `test_injection_flag_true_returns_injection_detected_without_claude_call` | 2 — Input Validation | `payload["injection_flag"]=True` → `injection_detected`, no Claude call made |
| 9 | `test_non_dict_payload_type_returns_invalid_input` | 2 — Input Validation | String passed as payload → `invalid_input`, no HTTP call made |
| 10 | `test_anthropic_authentication_error_returns_unauthenticated` | 3 — Authentication | SDK raises `AuthenticationError` (401) → `unauthenticated` |
| 11 | `test_github_token_empty_on_high_confidence_path_returns_partial` | 3 — Authentication | Claude returns high confidence, `GITHUB_TOKEN` is empty → `partial` with interpretation preserved, `pr_url=None` |
| 12 | `test_github_401_on_branch_creation_returns_partial` | 3 — Authentication | GitHub 401 on branch creation → `_open_draft_pr` returns `None` → `partial` |
| 13 | `test_anthropic_permission_denied_error_returns_unauthorized` | 4 — Authorization | `PermissionDeniedError` (403) from Anthropic → `unauthorized` |
| 14 | `test_github_403_on_pr_creation_returns_partial` | 4 — Authorization | GitHub 403 on PR creation → `partial` (interpretation still returned) |
| 15 | `test_anthropic_model_not_found_returns_invalid_input` | 5 — Not Found | `NotFoundError` (404) → `invalid_input` (model name in config doesn't exist — config error, not transient) |
| 16 | `test_github_repo_not_found_on_branch_fetch_returns_partial` | 5 — Not Found | `GET /branches` returns 404 → `_open_draft_pr` returns `None` → `partial` |
| 17 | `test_anthropic_rate_limit_returns_rate_limited_without_retry` | 6 — Rate Limiting | `RateLimitError` (429) → `rate_limited`; assert `client.messages.create` called exactly once (no retry inside agent) |
| 18 | `test_anthropic_server_error_returns_server_error` | 7 — Server Failures | `APIStatusError` 500 → `server_error` |
| 19 | `test_anthropic_timeout_returns_timeout` | 7 — Server Failures | `APITimeoutError` → `timeout` (distinct from network error) |
| 20 | `test_anthropic_connection_error_returns_network_error` | 7 — Network Failures | `APIConnectionError` → `network_error` (server unreachable) |
| 21 | `test_github_server_error_on_pr_creation_returns_partial` | 7 — Server Failures | GitHub 500 during PR creation → `_open_draft_pr` returns `None` → `partial` |
| 22 | `test_anthropic_bad_request_error_returns_invalid_input` | 7b — Anthropic 4xx | `BadRequestError` (400) — malformed tool definition or payload → `invalid_input` |
| 23 | `test_anthropic_conflict_error_returns_server_error` | 7b — Anthropic 4xx | `ConflictError` (409) — transient → `server_error` |
| 24 | `test_anthropic_unprocessable_entity_returns_invalid_input` | 7b — Anthropic 4xx | `UnprocessableEntityError` (422) — semantically invalid payload → `invalid_input` |
| 25 | `test_claude_response_with_no_tool_use_block_returns_schema_error` | 8 — Schema Validation | Claude responds with text-only (no `tool_use` block) → `schema_error` |
| 26 | `test_return_interpretation_missing_required_field_returns_schema_error` | 8 — Schema Validation | `tool_use` block present but `root_cause` field absent → `schema_error` |
| 27 | `test_return_interpretation_invalid_confidence_value_returns_schema_error` | 8 — Schema Validation | `confidence="very_high"` (not in enum `high\|medium\|low`) → `schema_error` |
| 28 | `test_return_interpretation_wrong_type_for_regression_returns_schema_error` | 8 — Schema Validation | `regression` is string `"true"` instead of bool → `schema_error` |
| 29 | `test_usage_by_turn_has_exactly_one_entry_after_single_claude_call` | Observability | `usage_by_turn` list has exactly 1 entry — confirms single-call design, no loop |
| 30 | `test_record_agent_run_called_with_correct_args_on_completed_path` | Observability | Mock `record_agent_run`; assert called with `"coding_agent"`, result dict, `usage_by_turn`, `issue_number` |
| 31 | `test_record_agent_run_called_on_invalid_input_path` | Observability | `record_agent_run` called even when `_validate_payload` returns an error — observability never skipped |
| 32 | `test_github_timeout_during_pr_flow_returns_partial` | 7 — Server Failures | `requests.Timeout` raised inside `_open_draft_pr` → `partial`; interpretation preserved, `pr_url=None` |
| 33 | `test_github_network_error_during_pr_flow_returns_partial` | 7 — Network Failures | `requests.ConnectionError` raised inside `_open_draft_pr` → `partial`; distinct from timeout — server unreachable |
| 34 | `test_github_server_error_on_branch_fetch_returns_partial` | 7 — Server Failures | GitHub 500 on `GET /branches` (step 1 of `_open_draft_pr`) → `partial`; confirms all 3 GitHub steps are error-safe, not just step 3 |

---

## 10. Files Touched

| File | Action | Notes |
|---|---|---|
| `agents/coding_agent.py` | Create | New agent module |
| `agents/config.py` | Modify | Add `GITHUB_PR_BRANCH_PREFIX` constant |
| `agents/tests/test_coding_agent.py` | Create | TDD test file — all tests written red first |
| `agents/specs/d6_coding_agent.md` | Create | This spec |
| `agents/specs/DEPENDENCY_MAP.md` | Modify | Add D.6 signatures after slice completes |

---

## 11. Acceptance Criteria

- [ ] All 34 new `test_coding_agent.py` tests pass
- [ ] Full suite passes with no regressions (107 + 34 = 141 tests)
- [ ] `status: completed` returned for a valid combined payload
- [ ] `interpretation.root_cause` is a non-empty string
- [ ] `pr_url` is non-null for high/medium confidence; `None` for low confidence
- [ ] `usage_by_turn` has exactly one entry (single Claude call confirmed)
- [ ] `record_agent_run` called before every return path (verified by mock in tests)
- [ ] `GITHUB_PR_BRANCH_PREFIX` used for branch name — no hardcoded `"fix/sentry-"` in code
- [ ] Smoke test: hand-assembled findings dict from real extractor outputs → `status: completed`, `pr_url` non-null
