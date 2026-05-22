# D.6 — Coding Agent Spec

**Architecture doc sections:** `Coding Agent`, `Agent Catalog`, `Principles`,
`Confidence-Gated Actions`, `Human in the Loop`, `Runbook Integration`,
`Compliance Awareness`, `Token Budget Targets`

---

## 1. What This Slice Builds

The Coding Agent is an **optional pipeline stage**. Teams that only need diagnosis can
stop at D.5 (Diagnostic Agent). Teams that want automated code fixes enable D.6 via
the Orchestrator config flag `enable_coding_agent: bool`.

When enabled, the Coding Agent receives D.5's structured diagnostic findings plus the
combined extractor payload, makes a **single Claude API call** to generate a targeted
code fix, commits that fix to a new feature branch via the GitHub Contents API, and
opens a **draft PR**. The draft PR contains real file changes — not a placeholder.

Claude's job is narrow: given the file content and D.5's diagnosis (`fix_type`,
`fix_detail`, `fix_location`), generate an `original_snippet` (exact lines to replace)
and a `replacement_snippet` (the fixed code). The agent verifies the original snippet
exists verbatim in the file before committing — this guards against Claude hallucinating
a location that doesn't exist.

**Multi-file fixes:** D.5 may identify more than one file needing changes (`fix_files`
is a list). The Coding Agent auto-commits only `fix_files[0]` (the primary fix). Any
remaining files in `fix_files[1:]` are listed in the PR description as requiring manual
attention — keeping the agent's blast radius small.

**This agent has no access to Sentry or Render.** Its external calls are one Anthropic
SDK call and, conditionally, one GitHub API call (open draft PR). The file patch and
commit are performed via local git operations — `git commit` fires pre-commit hooks
exactly as they would for a human engineer, then `git push` sends the branch to origin.

---

## 2. Where This Agent Runs

Unlike D.1–D.4 (which call external HTTP APIs and can run anywhere), the Coding Agent
writes to the local filesystem and runs git commands. It must run in a **git-enabled
environment** where:

- The repository is checked out and the working tree is clean
- `pre-commit` is installed and configured
- Git is configured with push credentials (via `GITHUB_TOKEN` as a credential helper)

This does **not** have to be the same runner or job as the Diagnostic Agent. Any
environment satisfying the three requirements above is valid — a GitHub Actions job
with `actions/checkout`, a self-hosted runner, or a local developer machine. What
matters is the capability, not co-location with D.5.

If the environment does not satisfy these requirements, the agent returns
`STATUS_INVALID_INPUT` without making any Claude or GitHub API call.

---

## 3. Signature

```python
def run(payload: dict, issue_number: str = "") -> dict:
    ...
```

**`payload`** — the combined findings dict assembled by the Orchestrator. Must contain
a `"diagnostic"` key with D.5's findings (including `fix_files`, `fix_location`,
`fix_type`, `fix_detail`). Also contains one or more source blocks (`sentry_frontend`,
`sentry_backend`, `render_logs`, `github`) plus merged `pii_flag` and `injection_flag`.

**`issue_number`** — GitHub issue number as a string (e.g. `"42"`); used as the suffix
in the PR branch name and passed to `record_agent_run`. Empty string when called outside
a GitHub issue context.

---

## 4. Guardrails Consumed

| Guardrail | Source | Type | Notes |
|---|---|---|---|
| `CODING_MAX_TURNS` | `agents/config.py` | `int` (= 1) | Bounds the single Claude call — not a loop limit |
| `CODING_MAX_TOKENS` | `agents/config.py` | `int` | Max output tokens per Claude response |
| `CODING_MODEL` | `agents/config.py` | `str` | Sonnet 4.6 — strongest reasoning for code generation |
| `GITHUB_API_BASE` | `agents/config.py` | `str` | Base URL for all GitHub API calls |
| `GITHUB_REPO` | `agents/config.py` | `str` | `owner/repo` slug |
| `GITHUB_TOKEN` | `agents/config.py` | `str` | Personal access token — write scope required |
| `GITHUB_BRANCH` | `agents/config.py` | `str` | Base branch for PR (default `"main"`) |
| `GITHUB_PR_BRANCH_PREFIX` | `agents/config.py` | `str` | Branch name prefix (default `"fix/sentry-"`) |

> **New constant required:** `GITHUB_PR_BRANCH_PREFIX = os.getenv("GITHUB_PR_BRANCH_PREFIX", "fix/sentry-")` in `agents/config.py`.

---

## 5. Return Shape

```python
{
    "status":          str,    # STATUS_COMPLETED | STATUS_NO_DATA | STATUS_PARTIAL
                               # | STATUS_INVALID_INPUT | STATUS_INJECTION_DETECTED
                               # | STATUS_UNAUTHENTICATED | STATUS_UNAUTHORIZED
                               # | STATUS_RATE_LIMITED | STATUS_SERVER_ERROR
                               # | STATUS_NETWORK_ERROR | STATUS_SCHEMA_ERROR
    "source":          "coding",
    "interpretation":  {       # present only when status == STATUS_COMPLETED or STATUS_PARTIAL
        "root_cause":       str,   # cross-source narrative, ~50-100 words
        "affected_layer":   str,   # "frontend" | "backend" | "graphql" | "database" | "unknown"
        "regression":       bool,  # True if first_seen is after pr_merged_at
        "confidence":       str,   # "high" | "medium" | "low"
        "recommended_fix":  str,   # actionable one-sentence fix directive
        "runbook_match":    str | None,
    },
    "file_changed":    str | None,   # fix_files[0] path if committed; None otherwise
    "remaining_files": list[str],    # fix_files[1:] — listed in PR but not auto-committed
    "commit_sha":      str | None,   # SHA of committed fix; None if no commit made
    "pr_url":          str | None,   # draft PR html_url; None if low confidence or PR failed
    "pii_flag":        bool,         # inherited from payload's merged pii_flag
    "injection_flag":  bool,         # inherited from payload's merged injection_flag
}
```

**`STATUS_COMPLETED`** — Claude returned a valid fix, snippet verified in file, commit
made, draft PR opened (or skipped for low confidence).

**`STATUS_PARTIAL`** — Claude returned a valid interpretation but one of the following
failed: snippet not found in file (hallucination guard triggered), GitHub file read
failed, GitHub commit failed, or GitHub PR creation failed. `interpretation` is still
returned; `pr_url` and `commit_sha` are `None`.

---

## 6. Implementation Rules

1. **Single Claude call only.** `CODING_MAX_TURNS` is 1. Call
   `client.messages.create()` exactly once per `run()` invocation.

2. **Use `build_system_prompt()`** from `agents/prompt_utils.py` to wrap the system
   prompt with `cache_control: ephemeral`. The system prompt does not change between
   runs — every cache hit saves ~90% on input tokens.

3. **System prompt instructs Claude:** given D.5's diagnosis (`fix_type`, `fix_detail`,
   `fix_location`) and the file content, generate `original_snippet` (exact lines to
   replace, must exist verbatim) and `replacement_snippet` (the fixed code). Do not
   refactor surrounding code. Do not touch lines outside the identified location.

4. **Pass file content in the user message.** Before calling Claude, read `fix_files[0]`
   via `_read_file_from_github()`. Include the full file content in the user message
   alongside D.5's diagnosis. Claude never needs to request files — it receives what it
   needs upfront. No agentic loop.

5. **Force structured output via `return_code_fix` tool.** Register a single tool
   definition (see `_build_tool_definitions()`). Pass `tool_choice={"type": "any"}` so
   Claude must call the tool. Parse the `tool_use` block to get the fix dict. If no
   `tool_use` block is present, return `STATUS_SCHEMA_ERROR`.

6. **Hallucination guard — verify before committing.** Call `_apply_patch()` with
   `original_snippet` against the file content. If `original_snippet` is not found
   verbatim, return `STATUS_PARTIAL` with `interpretation` preserved — do not commit.

7. **Confidence-gated GitHub flow:**
   - `high` or `medium` → execute all five GitHub API calls (get SHA → create branch →
     read file → commit file → open draft PR)
   - `low` → return `interpretation` only; `pr_url=None`, `commit_sha=None`; no GitHub
     API calls

8. **Auto-fix primary file only.** Commit only `fix_files[0]`. List `fix_files[1:]`
   in the PR description under "Also requires manual changes".

9. **PR branch pattern:** `{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{YYYYMMDDHHMMSS}`
   (e.g. `fix/sentry-42-20260519143022`). Timestamp suffix guarantees uniqueness across
   re-runs — no 422 "ref already exists" collision.

10. **`record_agent_run()` before every `return`.** Pass `usage_by_turn` (one entry
    from the single Claude call), the result dict, and `issue_number`.

11. **`confidence_to_numeric()`** — call before `record_agent_run()` to log confidence
    numerically.

12. **PII and injection flags** — inherit merged flags from `payload`. If
    `payload.get("injection_flag")` is `True`, return `STATUS_INJECTION_DETECTED`
    immediately without calling Claude or reading any file.

13. **All constants from `agents/config.py`** — no model names, URLs, branch prefixes,
    or token limits hardcoded in `coding_agent.py`.

14. **No cross-feature imports.** Import only from `agents/prompt_utils.py`,
    `agents/sentry_utils.py`, and `agents/config.py`.

---

## 7. Commit Flow (local git + one GitHub API call)

```
1. git checkout -b {branch_name}
        → creates and switches to new feature branch locally
        → branch_name: {GITHUB_PR_BRANCH_PREFIX}{issue_number}-{YYYYMMDDHHMMSS}

2. Write patched file content to local disk at fix_files[0]
        → replaces original_snippet with replacement_snippet in place

3. git add {fix_files[0]}
        → stages only the target file — never git add -A

4. git commit -m "{commit_message}"
        → pre-commit hooks fire here automatically
        → if hooks fail: agent returns STATUS_PARTIAL, no push made

5. git push origin {branch_name}
        → pushes branch to remote; uses GITHUB_TOKEN as credential

6. POST /repos/{owner}/{repo}/pulls  (single GitHub API call)
        body: { title, body, head: {branch_name}, base: {GITHUB_BRANCH}, draft: true }
        → opens draft PR; returns html_url
```

Any failure in steps 1–6 → `_commit_and_push()` or `_open_draft_pr()` returns `None`
→ caller sets `status=STATUS_PARTIAL`, `interpretation` preserved.

Pre-commit hook failure in step 4 is treated as `STATUS_PARTIAL` — the interpretation
is valid but the code change did not meet the team's quality bar. The PR is not opened.
The branch is cleaned up locally (checkout back to base, delete failed branch).

---

## 8. Exit Conditions

| Status | Trigger | What is returned |
|---|---|---|
| `STATUS_COMPLETED` | Claude returns valid `return_code_fix` tool call; snippet verified; commit made; PR opened (or low confidence — skipped) | Full dict with `interpretation`, `file_changed`, `commit_sha`, `pr_url` |
| `STATUS_PARTIAL` | Valid interpretation returned but snippet not found in file, or any GitHub API step failed | `interpretation` present; `file_changed`, `commit_sha`, `pr_url` all `None` |
| `STATUS_NO_DATA` | `payload` is empty, `"diagnostic"` key absent, or diagnostic status is `no_data` | Minimal dict with source |
| `STATUS_INVALID_INPUT` | `_validate_payload()` returns an error string | Minimal dict with error |
| `STATUS_INJECTION_DETECTED` | `payload.get("injection_flag")` is `True` | Minimal dict with source |
| `STATUS_UNAUTHENTICATED` | `APIStatusError` 401 from Anthropic, or `GITHUB_TOKEN` empty on confidence-gated path | Minimal dict with source |
| `STATUS_UNAUTHORIZED` | `APIStatusError` 403 from Anthropic or GitHub | Minimal dict with source |
| `STATUS_RATE_LIMITED` | `APIStatusError` 429 from Anthropic | Minimal dict with source |
| `STATUS_SERVER_ERROR` | `APIStatusError` 5xx from Anthropic or GitHub | Minimal dict with source |
| `STATUS_NETWORK_ERROR` | `APIConnectionError` or `requests.exceptions.ConnectionError` | Minimal dict with source |
| `STATUS_SCHEMA_ERROR` | No `tool_use` block in Claude response, or `return_code_fix` input fails schema check | Minimal dict with source |

---

## 9. Private Helper Functions

```python
def _validate_payload(payload: dict) -> str | None:
    # Returns an error string if:
    #   - payload is None, not a dict, or empty
    #   - "diagnostic" key is absent or its status is not "completed" or "partial"
    #   - diagnostic findings missing fix_files, fix_type, or fix_detail
    # Returns None if payload is usable.

def _build_tool_definitions() -> list[dict]:
    # Returns the Anthropic tool schema list with one tool: "return_code_fix".
    # Input schema fields:
    #   root_cause (string), affected_layer (enum: frontend|backend|graphql|database|unknown),
    #   regression (bool), confidence (enum: high|medium|low),
    #   recommended_fix (string), runbook_match (string or null),
    #   original_snippet (string — exact lines to replace, must exist verbatim in file),
    #   replacement_snippet (string — the corrected code replacing original_snippet).

def _parse_code_fix(response) -> dict | None:
    # Finds the first tool_use block in response.content where name=="return_code_fix".
    # Returns the block's "input" dict, or None if not found.

def _should_open_pr(confidence: str) -> bool:
    # Returns True only for "high" or "medium" confidence.

def _check_environment() -> str | None:
    # Verifies the agent is running in a git-enabled environment.
    # Checks: (1) current directory is inside a git repo (git rev-parse --git-dir);
    #         (2) working tree is clean (git status --porcelain returns empty);
    #         (3) pre-commit is installed (shutil.which("pre-commit") is not None);
    #         (4) GITHUB_TOKEN is non-empty.
    # Returns an error string describing the first failed check, or None if all pass.

def _apply_patch(file_content: str, original_snippet: str, replacement_snippet: str) -> str | None:
    # Checks that original_snippet exists verbatim in file_content.
    # Returns patched file content string on success.
    # Returns None if original_snippet is not found — hallucination guard.

def _commit_and_push(
    file_path: str, patched_content: str, branch_name: str, commit_message: str
) -> str | None:
    # Orchestrates local git steps 1–5:
    #   git checkout -b {branch_name}
    #   write patched_content to file_path on disk
    #   git add {file_path}
    #   git commit -m {commit_message}  ← pre-commit hooks fire here
    #   git push origin {branch_name}
    # Returns commit SHA on success (from git rev-parse HEAD after commit).
    # Returns None on any failure (hook failure, push error, etc.).
    # On failure: checks out base branch and deletes the failed branch to leave
    # the working tree clean.

def _format_pr_body(
    interpretation: dict, payload: dict, file_changed: str, remaining_files: list[str], issue_number: str
) -> str:
    # Builds the markdown PR description.
    # Includes: root cause summary, affected layer, confidence, recommended fix,
    #   file committed, remaining files requiring manual changes, evidence sources,
    #   link to GitHub issue (if issue_number non-empty).
    # Never includes raw code snippets, PII, or injection-flagged content.

def _open_draft_pr(
    branch_name: str, interpretation: dict, payload: dict,
    file_changed: str, remaining_files: list[str], issue_number: str
) -> str | None:
    # Single GitHub API call: POST /repos/{owner}/{repo}/pulls
    # Returns pr_html_url on success, None on any HTTP or network error.
    # Branch name already exists on remote (pushed in _commit_and_push).
```

---

## 10. TDD Test Plan

**Integrations under test:**
- Anthropic Claude API (SDK) — single `client.messages.create()` call, `return_code_fix` tool
- Local git (subprocess) — `git checkout -b`, `git add`, `git commit`, `git push`
- GitHub API (requests + Bearer token) — one call: POST /pulls

| # | Test name | Category | What it verifies |
|---|---|---|---|
| 1 | `test_high_confidence_returns_completed_with_pr_and_commit` | 1 — Happy Path | Valid payload, Claude returns high confidence fix, snippet found, git commit succeeds, PR opened → `status=completed`, `pr_url` and `commit_sha` populated, `file_changed` = `fix_files[0]` |
| 2 | `test_medium_confidence_returns_completed_with_pr_and_commit` | 1 — Happy Path | Medium confidence → same as test 1 |
| 3 | `test_low_confidence_returns_completed_without_pr_or_commit` | 1 — Happy Path | Low confidence → `status=completed`, `pr_url=None`, `commit_sha=None`, no git or GitHub API calls |
| 4 | `test_multi_file_fix_commits_only_primary_file` | 1 — Happy Path | `fix_files` has two entries → only `fix_files[0]` committed; `fix_files[1]` in `remaining_files`; PR body contains the remaining file name |
| 5 | `test_pr_branch_name_includes_issue_number_and_timestamp` | 1 — Happy Path | Branch name used in `git checkout -b` matches `{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{14-digit-timestamp}` |
| 6 | `test_file_content_passed_to_claude_in_user_message` | 1 — Happy Path | Local file content appears in the user message sent to Claude — confirms no agentic loop |
| 7 | `test_none_payload_returns_invalid_input_without_any_call` | 2 — Input Validation | `None` passed as payload → `invalid_input`, no Claude or git call made |
| 8 | `test_empty_dict_payload_returns_invalid_input` | 2 — Input Validation | `{}` → `invalid_input` |
| 9 | `test_missing_diagnostic_key_returns_invalid_input` | 2 — Input Validation | Payload with no `"diagnostic"` key → `invalid_input` |
| 10 | `test_diagnostic_status_no_data_returns_no_data` | 2 — Input Validation | `payload["diagnostic"]["status"] = "no_data"` → `no_data`, no Claude call |
| 11 | `test_injection_flag_true_returns_injection_detected` | 2 — Input Validation | `payload["injection_flag"]=True` → `injection_detected`, no Claude or git call |
| 12 | `test_non_dict_payload_returns_invalid_input` | 2 — Input Validation | String passed as payload → `invalid_input` |
| 13 | `test_invalid_environment_returns_invalid_input` | 2 — Input Validation | `_check_environment()` returns error (e.g. pre-commit not installed) → `invalid_input`, no Claude call |
| 14 | `test_snippet_not_found_in_file_returns_partial_with_interpretation` | 3 — Hallucination Guard | `original_snippet` not present verbatim in file → `STATUS_PARTIAL`, `interpretation` present, no commit made |
| 15 | `test_empty_original_snippet_returns_partial` | 3 — Hallucination Guard | `original_snippet=""` → `STATUS_PARTIAL` — empty snippet cannot be safely applied |
| 16 | `test_pre_commit_hook_failure_returns_partial_with_interpretation` | 3 — Hallucination Guard | `git commit` exits non-zero (hook rejects change) → `STATUS_PARTIAL`, `interpretation` present, `pr_url=None`; working tree restored to clean state |
| 17 | `test_anthropic_authentication_error_returns_unauthenticated` | 4 — Authentication | SDK raises `AuthenticationError` (401) → `unauthenticated` |
| 18 | `test_github_token_empty_detected_by_environment_check` | 4 — Authentication | `GITHUB_TOKEN` is `""` → `_check_environment()` catches it → `invalid_input` before any Claude call |
| 19 | `test_git_push_auth_failure_returns_partial` | 4 — Authentication | `git push` fails with auth error (exit code non-zero, stderr contains 403) → `partial`, `interpretation` preserved |
| 20 | `test_anthropic_permission_denied_returns_unauthorized` | 5 — Authorization | `PermissionDeniedError` (403) from Anthropic → `unauthorized` |
| 21 | `test_github_403_on_pr_creation_returns_partial` | 5 — Authorization | GitHub 403 on POST /pulls → `partial`, `commit_sha` present, `pr_url=None` |
| 22 | `test_anthropic_model_not_found_returns_invalid_input` | 6 — Not Found | `NotFoundError` (404) from Anthropic → `invalid_input` |
| 23 | `test_anthropic_rate_limit_returns_rate_limited_without_retry` | 7 — Rate Limiting | `RateLimitError` (429) → `rate_limited`; assert `client.messages.create` called exactly once |
| 24 | `test_anthropic_server_error_returns_server_error` | 8 — Server Failures | `APIStatusError` 500 → `server_error` |
| 25 | `test_anthropic_timeout_returns_timeout` | 8 — Server Failures | `APITimeoutError` → `timeout` |
| 26 | `test_anthropic_connection_error_returns_network_error` | 8 — Network Failures | `APIConnectionError` → `network_error` |
| 27 | `test_git_push_failure_returns_partial` | 8 — Server Failures | `git push` exits non-zero (remote error) → `partial`; working tree restored |
| 28 | `test_github_500_on_pr_creation_returns_partial` | 8 — Server Failures | GitHub 500 on POST /pulls → `partial`; `commit_sha` present (push succeeded), `pr_url=None` |
| 29 | `test_github_connection_error_on_pr_creation_returns_partial` | 8 — Network Failures | `requests.ConnectionError` on POST /pulls → `partial` |
| 30 | `test_anthropic_bad_request_returns_invalid_input` | 9 — Anthropic 4xx | `BadRequestError` (400) → `invalid_input` |
| 31 | `test_anthropic_conflict_returns_server_error` | 9 — Anthropic 4xx | `ConflictError` (409) → `server_error` |
| 32 | `test_anthropic_unprocessable_entity_returns_invalid_input` | 9 — Anthropic 4xx | `UnprocessableEntityError` (422) → `invalid_input` |
| 33 | `test_claude_response_with_no_tool_use_returns_schema_error` | 10 — Schema Validation | Text-only Claude response → `schema_error` |
| 34 | `test_missing_original_snippet_field_returns_schema_error` | 10 — Schema Validation | `tool_use` block present but `original_snippet` field absent → `schema_error` |
| 35 | `test_invalid_confidence_value_returns_schema_error` | 10 — Schema Validation | `confidence="very_high"` → `schema_error` |
| 36 | `test_regression_wrong_type_returns_schema_error` | 10 — Schema Validation | `regression="true"` (string not bool) → `schema_error` |
| 37 | `test_usage_by_turn_has_exactly_one_entry` | 11 — Observability | `usage_by_turn` list has exactly 1 entry — confirms single-call design |
| 38 | `test_record_agent_run_called_on_completed_path` | 11 — Observability | Mock `record_agent_run`; assert called with `"coding_agent"`, result dict, `usage_by_turn`, `issue_number` |
| 39 | `test_record_agent_run_called_on_invalid_input_path` | 11 — Observability | `record_agent_run` called even when `_validate_payload` fails — observability never skipped |
| 40 | `test_git_commit_called_before_pr_opened` | 11 — Observability | Assert `git commit` subprocess call precedes POST /pulls — order enforced |
| 41 | `test_working_tree_clean_after_hook_failure` | 11 — Observability | After pre-commit hook failure, assert no uncommitted changes remain and failed branch is deleted |

---

## 11. Files Touched

| File | Action | Notes |
|---|---|---|
| `agents/coding_agent.py` | Create | New agent module |
| `agents/config.py` | Modify | Add `GITHUB_PR_BRANCH_PREFIX` constant |
| `agents/tests/test_coding_agent.py` | Create | TDD test file — all tests written red first |
| `agents/specs/d6_recommendation_agent.md` | Modify | This spec — replaces the placeholder version |
| `agents/specs/DEPENDENCY_MAP.md` | Modify | Add D.6 signatures after slice completes |

---

## 12. Acceptance Criteria

- [ ] All 41 new `test_coding_agent.py` tests pass
- [ ] Full suite passes with no regressions (107 + 41 = 148 tests)
- [ ] `status: completed` returned for a valid payload with a verifiable snippet
- [ ] `file_changed` is `fix_files[0]`; `remaining_files` contains `fix_files[1:]`
- [ ] `pr_url` and `commit_sha` are non-null for high/medium confidence; `None` for low
- [ ] `original_snippet` not found in file → `STATUS_PARTIAL`, no commit made
- [ ] Pre-commit hook failure → `STATUS_PARTIAL`, working tree restored to clean state
- [ ] `usage_by_turn` has exactly one entry (single Claude call confirmed)
- [ ] `record_agent_run` called before every return path (verified by mock in tests)
- [ ] `GITHUB_PR_BRANCH_PREFIX` used in branch name — no hardcoded `"fix/sentry-"` in code
- [ ] PR draft flag is `true` — never opens a ready-to-merge PR automatically
- [ ] Smoke test: hand-assembled findings dict from real D.5 output → `status: completed`, `pr_url` non-null, actual code change visible in GitHub PR diff, pre-commit hooks confirmed to have run
