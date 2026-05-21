# D.4 — GitHub Extractor Spec

**Status: APPROVED — signed off by Vikas, 2026-05-14**
**Architecture doc sections:** `GitHub Agent Query Contract`, `Agent Catalog`, `Finding Schema`, `GitHub Findings Schema`
**Dependency map:** `agents/specs/DEPENDENCY_MAP.md`

---

## What this slice builds

A pure Python extractor (`agents/github_extractor.py`) that queries the GitHub REST API to fetch commits that went into the release where the error first appeared, and returns a structured dict to the Orchestrator. Zero Claude API calls.

---

## Signature

```python
# agents/github_extractor.py
def run(guardrails: dict, issue_number: str = "") -> dict:
    ...
```

**Guardrails consumed:**

| Key | Type | Source | Notes |
|---|---|---|---|
| `max_commits` | `int` | Orchestrator | Overrides `GITHUB_MAX_COMMITS`; defaults to config value if absent. Must be ≤ 100 — GitHub's `per_page` platform cap; values above 100 silently return 100, masking the true limit, so `_validate_guardrails` rejects them as `invalid_input` |
| `max_files_per_commit` | `int` | Orchestrator | Overrides `GITHUB_MAX_FILES_PER_COMMIT`; caps the `changed_files` list per commit |
| `release_sha` | `str \| None` | Orchestrator | Sentry release SHA; if provided, walk commits backwards from this SHA (not HEAD) — these are the commits that went into the failing release |

---

## Return Shape

Matches the `GitHub Findings Schema` section in `agent-architecture.md`.

```python
{
    "status": "completed",        # see Exit Conditions for full status set
    "source": "github",
    "commit_window": {
        "branch": "main",
        "from_sha": "a3f9c12",   # oldest commit returned (N commits before the anchor)
        "to_sha":   "cfe6747"    # release_sha anchor, or HEAD if no release_sha provided
    },
    "commit_count": 2,
    "commits": [
        {
            "sha": "cfe6747",
            "message": "fix: remove allergens from useMenu GraphQL query",
            "author": "vikasparth",
            "committed_at": "2026-05-04T08:45:00Z",
            "changed_files": ["src/hooks/useMenu.ts", "src/features/menu/types.ts"]
        }
    ],
    "injection_flag": False,
    "pii_flag": False
}
```

Error statuses (`unauthenticated`, `unauthorized`, `rate_limited`, `server_error`, `network_error`, `timeout`, `not_found`, `invalid_input`, `schema_error`) return a minimal dict:

```python
{"status": "<status>", "source": "github"}
```

---

## Implementation Rules

1. Import `GITHUB_API_BASE`, `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_BRANCH`, `GITHUB_MAX_COMMITS`, `GITHUB_MSG_MAX_LEN`, `GITHUB_MAX_FILES_PER_COMMIT` from `agents/config.py` — never hardcode.
2. Import `_INJECTION_RE`, `_EMAIL_RE`, `_PHONE_RE` from `agents/patterns.py` — never redefine locally.
3. Import `record_agent_run` from `agents/sentry_utils.py` — call it before every `return`.
4. Use `STATUS_COMPLETED`, `STATUS_NO_DATA`, `STATUS_INJECTION_DETECTED` constants from `agents/config.py`.
5. `usage_by_turn = []` — pure Python extractor, no Claude calls, list stays empty.
6. Author email must be dropped unconditionally — keep only GitHub `login` field.
7. Commit message trimmed to first line, capped at `GITHUB_MSG_MAX_LEN` chars.
8. Each commit detail call (`GET /repos/{repo}/commits/{sha}`) fetches changed files — keep only `filename`.
9. Guardrail validation runs before any HTTP call — invalid input must never reach the GitHub API.
10. Reject `max_commits > 100` in `_validate_guardrails` — GitHub silently caps `per_page` at 100, so values above it would return fewer commits than requested with no error, making the cap invisible.

---

## Filtering Pipeline (ordered)

1. **Validate guardrails** — check types and value ranges before any HTTP call. Return `invalid_input` immediately on failure (see Exit Conditions).
2. **Check token** — if `GITHUB_TOKEN` is empty, return `unauthenticated` immediately. No HTTP call.
3. **Choose the walk anchor** — if `release_sha` is non-empty, set `sha={release_sha}` in the query; otherwise use `sha={GITHUB_BRANCH}` (HEAD). The GitHub API walks backwards from the given SHA, so passing the release SHA returns the commits that went into that release, not commits made after it.
4. **Fetch commit list** — `GET /repos/{repo}/commits?sha={anchor}&per_page={max_commits}`. Handle HTTP error codes and network exceptions before reading the response body (see Exit Conditions).
5. **Validate response schema** — confirm each commit object has `sha`, `commit.message`, `commit.author.date`, and `author.login`. Return `schema_error` if any are missing.
6. **Injection check** — for each commit message, test against `_INJECTION_RE`. On match → return `injection_detected` immediately.
7. **PII check** — for each commit message, test against `_EMAIL_RE` and `_PHONE_RE`. On match → `pii_flag=True` (do not return early — strip the match and continue). Author email is always dropped unconditionally regardless of this flag.
8. **Trim message** — keep first line only, capped at `GITHUB_MSG_MAX_LEN` chars.
9. **Fetch changed files** — for each commit, call `GET /repos/{repo}/commits/{sha}` and extract `files[*].filename`. Cap the list at `max_files_per_commit`. Apply the same HTTP error handling as step 4.

---

## Exit Conditions

| Status | Trigger | Orchestrator action |
|---|---|---|
| `completed` | At least one commit found in the window | Pass to Coding Agent |
| `no_data` | Zero commits after filtering | Skip GitHub findings in payload |
| `injection_detected` | Injection pattern matched in any commit message | Flag on GitHub Issue; stop processing |
| `invalid_input` | Guardrails dict has wrong types or malformed values (e.g. `max_commits="three"`, `max_commits=150`, `release_sha="not-a-sha!!"`, negative int) | Log misconfiguration; skip GitHub findings |
| `unauthenticated` | `GITHUB_TOKEN` is empty, or API returns 401 | Alert owner — token missing or expired |
| `unauthorized` | API returns 403 | Alert owner — token lacks required scope (`Contents: Read`) |
| `not_found` | API returns 404 | Alert owner — `GITHUB_REPO` is wrong or `release_sha` does not exist |
| `rate_limited` | API returns 429 | Back off; retry at next scheduled run |
| `server_error` | API returns 5xx | Treat as transient; retry at next scheduled run |
| `timeout` | `requests` raises `Timeout` | Treat as transient; retry at next scheduled run |
| `network_error` | `requests` raises `ConnectionError` | Treat as transient; retry at next scheduled run |
| `schema_error` | Response body missing expected fields (`sha`, `commit.message`, `author.login`) | Log unexpected API shape; skip GitHub findings |

---

## Private Helper Functions

```python
def _validate_guardrails(guardrails: dict) -> str | None:
    # returns an error message string if invalid, None if valid
    ...

def _fetch_commits(anchor_sha: str, max_commits: int) -> list[dict]:
    # GET /repos/{GITHUB_REPO}/commits?sha={anchor_sha}&per_page={max_commits}
    # anchor_sha is release_sha when provided, otherwise GITHUB_BRANCH (HEAD)
    ...

def _fetch_changed_files(sha: str, max_files: int) -> list[str]:
    # GET /repos/{GITHUB_REPO}/commits/{sha} — returns filenames only, capped at max_files
    ...

def _trim_commit(raw: dict) -> dict:
    # injection check, PII check, message trim, drop email
    # returns trimmed dict with injection_flag and pii_flag as side-channel bools
    ...
```

Return flags (`injection_flag`, `pii_flag`) are accumulated across all commits in `run()` — a single True anywhere in the list sets the top-level flag.

---

## TDD Test Plan

File: `agents/tests/test_github_extractor.py`

| # | Test name | What it verifies |
|---|---|---|
| 1 | `test_returns_completed_with_commits` | Happy path: 3 commits returned → `status="completed"`, correct `commit_count`, `source="github"` |
| 2 | `test_no_data_when_api_returns_empty` | API returns `[]` → `status="no_data"`, `commit_count=0` |
| 3 | `test_injection_in_commit_message_returns_early` | One commit message contains injection pattern → `status="injection_detected"`, `injection_flag=True` |
| 4 | `test_author_email_is_stripped` | Raw GitHub response includes author email → returned dict has no email field anywhere |
| 5 | `test_release_sha_used_as_walk_anchor` | `release_sha` provided → fetch called with `sha=release_sha`, not `sha=GITHUB_BRANCH` |
| 6 | `test_message_trimmed_to_first_line_and_capped` | Multi-line commit message → only first line returned, capped at `GITHUB_MSG_MAX_LEN` |
| 7 | `test_max_commits_guardrail_is_respected` | `guardrails={"max_commits": 3}` → fetch called with `per_page=3`, `commit_count=3` |
| 8 | `test_max_files_per_commit_guardrail_is_respected` | API returns 50 files for a commit; `guardrails={"max_files_per_commit": 5}` → `changed_files` has exactly 5 entries |
| 9 | `test_missing_token_returns_unauthenticated` | `GITHUB_TOKEN` is empty → `status="unauthenticated"`, no HTTP call made |
| 10 | `test_401_response_returns_unauthenticated` | API returns 401 → `status="unauthenticated"` |
| 11 | `test_403_response_returns_unauthorized` | API returns 403 → `status="unauthorized"` |
| 12 | `test_404_response_returns_not_found` | API returns 404 → `status="not_found"` |
| 13 | `test_429_response_returns_rate_limited` | API returns 429 → `status="rate_limited"` |
| 14 | `test_5xx_response_returns_server_error` | API returns 500 → `status="server_error"` |
| 15 | `test_timeout_returns_timeout` | `requests` raises `Timeout` → `status="timeout"` |
| 16 | `test_connection_error_returns_network_error` | `requests` raises `ConnectionError` → `status="network_error"` |
| 17 | `test_invalid_max_commits_type_returns_invalid_input` | `guardrails={"max_commits": "three"}` → `status="invalid_input"`, no HTTP call made |
| 18 | `test_invalid_release_sha_format_returns_invalid_input` | `guardrails={"release_sha": "not-a-sha!!"}` → `status="invalid_input"`, no HTTP call made |
| 19 | `test_negative_max_files_returns_invalid_input` | `guardrails={"max_files_per_commit": -1}` → `status="invalid_input"`, no HTTP call made |
| 20 | `test_missing_response_fields_returns_schema_error` | API returns commit objects missing `author.login` → `status="schema_error"` |
| 21 | `test_record_agent_run_called_on_every_return` | Mock `record_agent_run` — assert called for both `completed` and `no_data` paths |
| 22 | `test_max_commits_above_platform_limit_returns_invalid_input` | `guardrails={"max_commits": 101}` → `status="invalid_input"`, no HTTP call made |

All HTTP calls mocked with `unittest.mock.patch`. No real GitHub API calls in tests.

---

## Files Touched

| File | Change |
|---|---|
| `agents/github_extractor.py` | New — implementation |
| `agents/tests/test_github_extractor.py` | New — 21 TDD tests |
| `agents/specs/DEPENDENCY_MAP.md` | Update — add `github_extractor` row and new config constants |
| `agents/.env.example` | Add `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_BRANCH` entries |

---

## Acceptance Criteria

- [ ] All 22 tests green
- [ ] Full test suite green (no regressions — currently 54 tests)
- [ ] No real GitHub API calls in tests (all mocked)
- [ ] `record_agent_run` called on every return path
- [ ] Guardrail validation runs before any HTTP call
- [ ] No hardcoded values — all config from `agents/config.py`
- [ ] No cross-feature imports — all shared helpers from `patterns.py`, `sentry_utils.py`, `config.py`
