# D.4 — GitHub Extractor Spec

**Status: DRAFT — awaiting sign-off**
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
| `max_commits` | `int` | Orchestrator | Overrides `GITHUB_MAX_COMMITS`; defaults to config value if absent |
| `max_files_per_commit` | `int` | Orchestrator | Overrides `GITHUB_MAX_FILES_PER_COMMIT`; caps the `changed_files` list per commit |
| `release_sha` | `str \| None` | Orchestrator | Sentry release SHA; if provided, walk commits backwards from this SHA (not HEAD) — these are the commits that went into the failing release |

---

## Return Shape

Matches the `GitHub Findings Schema` section in `agent-architecture.md`.

```python
{
    "status": "completed",        # "completed" | "no_data" | "injection_detected"
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

---

## Implementation Rules

1. Import `GITHUB_API_BASE`, `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_BRANCH`, `GITHUB_MAX_COMMITS`, `GITHUB_MSG_MAX_LEN` from `agents/config.py` — never hardcode.
2. Import `_INJECTION_RE`, `_EMAIL_RE`, `_PHONE_RE` from `agents/patterns.py` — never redefine locally.
3. Import `record_agent_run` from `agents/sentry_utils.py` — call it before every `return`.
4. Use `STATUS_COMPLETED`, `STATUS_NO_DATA`, `STATUS_INJECTION_DETECTED` constants from `agents/config.py`.
5. `usage_by_turn = []` — pure Python extractor, no Claude calls, list stays empty.
6. Author email must be dropped unconditionally — keep only GitHub `login` field.
7. Commit message trimmed to first line, capped at `GITHUB_MSG_MAX_LEN` chars.
8. Each commit detail call (`GET /repos/{repo}/commits/{sha}`) fetches changed files — keep only `filename`.

---

## Filtering Pipeline (ordered)

1. **Choose the walk anchor** — if `release_sha` is non-empty, set `sha={release_sha}` in the query; otherwise use `sha={GITHUB_BRANCH}` (HEAD). The GitHub API walks backwards from the given SHA, so passing the release SHA returns the commits that went into that release, not commits made after it.
2. **Fetch commit list** — `GET /repos/{repo}/commits?sha={anchor}&per_page={max_commits}`. Returns up to `max_commits` commits walking backwards from the anchor.
3. **Injection check** — for each commit message, test against `_INJECTION_RE`. On match → `injection_flag=True`, return immediately.
4. **PII check** — for each commit message, test against `_EMAIL_RE` and `_PHONE_RE`. On match → `pii_flag=True` (do not return early — strip the match and continue). Author email is always dropped unconditionally regardless of this flag.
5. **Trim message** — keep first line only, capped at `GITHUB_MSG_MAX_LEN` chars.
6. **Fetch changed files** — for each commit, call `GET /repos/{repo}/commits/{sha}` and extract `files[*].filename`. Cap the list at `max_files_per_commit` — a large refactor commit must not blow the token budget.

---

## Private Helper Functions

```python
def _fetch_commits(anchor_sha: str, max_commits: int) -> list[dict]:
    # GET /repos/{GITHUB_REPO}/commits?sha={anchor_sha}&per_page={max_commits}
    # anchor_sha is release_sha when provided, otherwise GITHUB_BRANCH (HEAD)
    ...

def _fetch_changed_files(sha: str) -> list[str]:
    # GET /repos/{GITHUB_REPO}/commits/{sha} — returns filenames only
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
| 7 | `test_max_commits_guardrail_is_respected` | Pass `guardrails={"max_commits": 3}` with API returning 10 commits → fetch called with `per_page=3`, `commit_count=3` |
| 8 | `test_max_files_per_commit_guardrail_is_respected` | Commit detail returns 50 changed files; `GITHUB_MAX_FILES_PER_COMMIT=5` → `changed_files` list has exactly 5 entries |
| 9 | `test_record_agent_run_called_on_every_return` | Mock `record_agent_run` — assert it is called for both completed and no_data paths |

All HTTP calls mocked with `unittest.mock.patch`. No real GitHub API calls in tests.

---

## Files Touched

| File | Change |
|---|---|
| `agents/github_extractor.py` | New — implementation |
| `agents/tests/test_github_extractor.py` | New — 7 TDD tests |
| `agents/specs/DEPENDENCY_MAP.md` | Update — add `github_extractor` row and new config constants |
| `agents/.env.example` | Add `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_BRANCH` entries |

---

## Acceptance Criteria

- [ ] All 9 tests green
- [ ] Full test suite green (no regressions — currently 25 tests)
- [ ] No real GitHub API calls in tests (all mocked)
- [ ] `record_agent_run` called on every return path
- [ ] No hardcoded values — all config from `agents/config.py`
- [ ] No cross-feature imports — all shared helpers from `patterns.py`, `sentry_utils.py`, `config.py`
