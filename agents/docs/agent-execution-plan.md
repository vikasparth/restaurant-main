# Agent Implementation Execution Plan — Aap ki Rasoi

**Status: IN PROGRESS**
**Last updated: 2026-05-28 (session 14)**
**Reference:** See `docs/engineering-practices/agent-architecture.md` for design decisions, access matrix, and finding schema.
**Master plan reference:** See `execution-plan.md` — Phase 3, Agentic Workflows.

---

## Current Focus

**Next: E.1 — Orchestrator design**

Session 14 complete (2026-05-28):
- **D.6 smoke test passed** — `status: completed`, `confidence: high`, PR #118 opened on GitHub, Sentry received 2 events ✅
- **`text=True` bug found and fixed** — `_check_environment()` was comparing `bytes` stdout to `str ""` (always True in Python 3); added `text=True` to both `subprocess.run` calls; bug was hidden by mocks in all 149 unit tests — only caught by the smoke test
- **pytest scoped to `agents/tests/`** — `_commit_and_push` was running `pytest -q` from repo root, collecting backend tests that need a separate venv; scoped to `agents/tests/` to unblock smoke test; full unified test runner is the production target when venvs are consolidated
- **smoke test PR #118 closed** — branch deleted, catering bug reverted; `smoke/bug` branch left for session cleanup
- **`agents/smoke_tests/smoke_d6.py` written** — targets a real logical bug (inverted operator in `catering_service.py`); demonstrates full pipeline: Claude API → hallucination guard → commit → PR

Session 13 complete (2026-05-26):
- **`run()` fully implemented** — Claude call block, hallucination guard, commit/PR flow all complete
- **42/42 tests green** — all coding agent tests passing; 107 + 42 = 149 total tests passing, no regressions
- **`DEPENDENCY_MAP.md` updated** — Coding Agent section added with all helper signatures, payload shape, return shape, branch naming pattern; `GITHUB_PR_BRANCH_PREFIX` and `CODING_MAX_TOKENS` constants added to config table
- **`_check_environment()` bug fixed** — changed `git status --porcelain` to `--untracked-files=no` so untracked files don't incorrectly block the agent
- **`confidence_numeric` added to interpretation dict** — `confidence_to_numeric()` now called before `record_agent_run()` as required by observability rules
- **`agents/` added to pre-commit config** — black and flake8 hooks now cover `^agents/` files; same rev as backend hooks
- **black + flake8 clean** — `coding_agent.py` passes both checks; unused imports removed (`os`, `STATUS_NOT_FOUND`)
- **D.6 changes committed and pushed** — implementation on `feat/d6-coding-agent` (merged); formatting fixes on same branch (pending commit + push)

**D.6 ✅ Done** — smoke test passed 2026-05-28; PR #118 verified and closed.

Session 10 complete (2026-05-20):
- **D.5 spec updated:** `fix_location` split into `fix_files: list[str]` (machine-readable, primary fix file first — supports multi-file fixes) and `fix_location: str` (human-readable location within `fix_files[0]` — passed to Claude as context)
- **D.6 spec fully rewritten:** true Coding Agent generating real code changes, not a placeholder PR
- **D.6 is now an optional pipeline stage:** Orchestrator config flag `enable_coding_agent: bool` — teams that only need diagnosis stop at D.5; teams wanting automated fixes enable D.6
- **D.6 commit flow:** local `git commit` + `git push` (not GitHub Contents API) — pre-commit hooks fire automatically on `git commit`, same as any engineer; single GitHub API call (POST /pulls) to open draft PR
- **D.6 environment requirement:** must run in a git-enabled environment where repo is checked out, `pre-commit` is installed, and `GITHUB_TOKEN` is available — does not have to be the same runner as D.5
- **D.6 multi-file fixes:** auto-commits `fix_files[0]` only; `fix_files[1:]` listed in PR description as requiring manual attention
- **D.6 hallucination guard:** `original_snippet` must exist verbatim in the file before any commit — prevents Claude hallucinating a location that doesn't exist
- **D.6 42 TDD tests planned** — covers happy path, hallucination guard, pytest failure, pre-commit hook failure, working tree cleanup, environment check, Anthropic errors, GitHub PR API errors
- **Architecture doc updated:** Coding Agent access, responsibility, and separation-of-concerns rationale reflect new design
- **Dependency map updated:** D.6 dependencies include `fix_files`, `subprocess`, `shutil.which`
- **Learning log:** new entry — agent-generated code must follow same engineering guardrails as human-written code (pre-commit hooks, branch conventions, CI gates)
- **Correction:** D.5 does NOT post to GitHub issues — the Orchestrator does (architecture doc line 667 is authoritative)

Session 9 complete (2026-05-20):
- **Agent rename:** Codebase Agent → Diagnostic Agent; Recommendation Agent → Coding Agent — reflects actual responsibilities
- **Coding Agent redesign:** no longer a cross-source synthesiser; follows Sentry Seer's pattern — Diagnostic Agent does analysis + fix plan, Coding Agent implements it; rationale: analysis and implementation are distinct concerns with different access requirements
- **Why Coding Agent is pluggable:** standardised handoff payload (`fix_files`, `fix_type`, `fix_detail`) means the coding step can be swapped to a different model or agent without touching the analysis layer
- All agent renames applied across docs, specs, ADRs, config constants, source strings, and Python files; 31 tests passing ✅
- Code renamed: `codebase_agent.py` → `diagnostic_agent.py`, `test_codebase_agent.py` → `test_diagnostic_agent.py`
- Config renamed: `CODEBASE_*` → `DIAGNOSTIC_*`, `RECOMMENDATION_*` → `CODING_*`

Session 8 complete (2026-05-19):
- D.ST.5a completed: Option A (stub trim) implemented, smoke tested, and strategy refined
- `agents/diagnostic_agent.py` — `_STUB` constant added, stub trim block added (commented out — blanket trim harms accuracy)
- Key finding: Claude needs prior file content across turns to confirm findings; stubbing too aggressively after one turn caused it to miss `allergens` and return a different root cause
- Refined guardrail: trim only fully-consumed results that won't be needed for future reasoning — not every result after one turn
- `agents/CLAUDE.md` — Token Efficiency guardrail updated with nuanced rule
- `agents/smoke_tests/smoke_dst5a.py` — new smoke test script for live token instrumentation
- `agents/tests/test_diagnostic_agent.py` — stub trim test added then commented out (32 tests, 107 suite) pending smarter strategy
- `docs/learning-log.md` — new entry: agentic loop processed tool results trim nuance
- D.ST.5a ✅ Done, D.6 is next

Session 7 complete (2026-05-18):
- `agents/specs/d5_diagnostic_agent.md` — Appendix fully documented: root cause of 11k token spike, fixed overhead breakdown, correct stub timing (shrink AFTER API response, not after append), full turn-by-turn round-trip schema showing exact `messages` list indices + `response.content` blocks + `tool_results` built per turn, concrete token savings table (3,065 tokens at Turn 4 vs ~8,485 without stub), three architectural fix options with tradeoffs
- Key insight: previous turn file content must stay FULL in messages until Claude responds in the NEXT turn — that response is proof Claude has processed it; only then is the shrink safe

Session 6 complete (2026-05-16):
- D.ST.5 smoke test passed: `status: completed`, `root_cause_file: src/features/menu/hooks/useMenu.ts`, `missing_field: allergens`, `fix_detail` actionable; Sentry received 2 events ✅
- `agents/diagnostic_agent.py` — two bugs found and fixed during smoke test:
  1. Agentic loop only handled the first `tool_use` block per turn (`next()`) — Claude can return multiple in one turn; fix: collect all blocks, send one `tool_result` per `tool_use`
  2. `record_agent_run` called with wrong keyword args (`source=`, `status=`) instead of `(agent_name, result_dict, usage_by_turn, issue_number)`; fix: added `_record_and_return` helper, all 17 call sites corrected
- `agents/github_extractor.py` — same `record_agent_run` signature bug fixed (latent — only survived because `AGENTS_SENTRY_DSN` unset in tests causes early return before `.get()` access); `_record_and_return` helper added, all 10 call sites corrected
- `agents/tests/test_diagnostic_agent.py` — 31st test added: `test_claude_multiple_tool_calls_in_one_turn_all_get_results`; `_sdk_response_multi` builder added
- `.claude/skills/api-integration-tests/skill.md` — Category 7c added: agentic loop invariants (multi-tool-use pattern) for Claude SDK agents
- `src/features/menu/hooks/useMenu.ts` — `allergens` field restored to MENU_QUERY (closes task 3.16.15)
- Full suite: 107/107 passing ✅

Key decisions made in session 6:
- Input tokens hit 11k on the failed smoke test run (Sonnet model + `max_files_to_read: 8` + multi-turn accumulation); clean run with `max_files_to_read: 3` stayed well under; token budget target of 5k was written for Haiku — Sonnet will naturally cost more; revisit when Orchestrator token cap is designed
- `fix_type` returned `missing_field` (not `add_field`/`remove_field` as spec predicted) — semantically equivalent, no change needed
- `_record_and_return` helper pattern is now the standard for all agents — DRY, avoids duplicating status string in both `record_agent_run` call and return dict

D.5 TDD complete (2026-05-15):
- `agents/tests/test_diagnostic_agent.py` — 30 tests written, all red (diagnostic_agent.py did not exist yet)
- `agents/config.py` — `STATUS_PARTIAL = "partial"` added ✅; `DIAGNOSTIC_MAX_FILE_CHARS = 10000` added ✅
- Tests cover: happy path (4), input validation (4), authentication (4), authorization (1), not found (1), rate limiting (1), server failures (2), network (2), schema validation (2), filesystem (5), observability (4)

D.5 spec complete (2026-05-15):
- `agents/specs/d5_diagnostic_agent.md` — spec signed off; 30 TDD tests defined across 8 categories
- `docs/engineering-practices/agent-architecture.md` — `Diagnostic Agent Query Contract` section added; `endpoint` input added (Render logs fallback when backend Sentry not yet instrumented — task 3.14 pending); `Where This Agent Runs` section added (GitHub Actions runner, checkout required); `DIAGNOSTIC_MAX_FILE_CHARS` guardrail row added (10000 chars ~2.5k tokens)
- Key design decisions: `return_findings` tool captures Claude's answer (no free-text parsing); `crash_location` + `endpoint` dual navigation start; Anthropic SDK error codes fully mapped (400→invalid_input, 401→unauthenticated, 403→unauthorized, 404→invalid_input, 409→server_error, 422→invalid_input, 429→rate_limited, 5xx→server_error)

Skills updated (2026-05-15):
- `api-integration-tests` skill — Category 7b added: Anthropic SDK error codes + exception hierarchy pattern
- `spec` agents profile — `test_skills` condition updated: trigger on any outbound HTTP call regardless of SDK/library used

D.4 complete (2026-05-15):
- `agents/github_extractor.py` ✅ — all 4 helpers + `run()` implemented
- All 22 D.4 tests green; full suite 76/76 passing (no regressions)
- `agents/specs/DEPENDENCY_MAP.md` — updated with `github_extractor` signatures ✅

D.4 implementation notes:
- `_validate_guardrails()` — type checks, bool guard, max_commits ≤ 100 (GitHub platform cap), SHA format via `_VALID_SHA_RE`
- `_fetch_commits()` — GET commits list, Bearer auth header, `raise_for_status()` bubbles errors to `run()`
- `_fetch_changed_files()` — GET per-commit detail, filenames only, cap applied both inside helper and in `run()` (mock-safe)
- `_trim_commit()` — injection early-return, PII flag accumulation, first-line + length cap, email never read
- `run()` — guardrail validation → token check → anchor (release_sha or HEAD) → try/except fetch → schema validation → commit loop → result dict

D.4 spec finalised (2026-05-14):
- `agents/specs/d4_github_extractor.md` — spec signed off (PR #95/#96 merged); filtering pipeline updated: guardrail validation + token check run as steps 1–2 before any HTTP call; error return shape added `{"status": "<status>", "source": "github"}`; test 22 added (`test_max_commits_above_platform_limit_returns_invalid_input`) — GitHub caps `per_page` at 100, values above silently return 100 so guardrail rejects them as `invalid_input`; total 22 TDD tests
- `agents/config.py` — 9 shared status constants added: `STATUS_INVALID_INPUT`, `STATUS_UNAUTHENTICATED`, `STATUS_UNAUTHORIZED`, `STATUS_NOT_FOUND`, `STATUS_RATE_LIMITED`, `STATUS_SERVER_ERROR`, `STATUS_TIMEOUT`, `STATUS_NETWORK_ERROR`, `STATUS_SCHEMA_ERROR`

Skills and tooling added (2026-05-14):
- `/api-integration-tests` skill — Category 9 (Pagination) added as mandatory conditional category; Test Structure Rules section added: no hardcoded config values, module-level mock constants, spread for variations, patch at helper boundary not `requests.get`, always patch `record_agent_run`
- `/spec` skill created — universal spec workflow: asks user for execution plan, architecture doc, and layer; loads layer profile; reads architecture sections via grep/offset; reads dependency map; generates spec from profile template; waits for sign-off; invokes test skills listed in profile; falls back to direct test plan generation if no test skills defined
- `/spec` agents profile created — structure-only: 11 required spec sections in order, dependency map path, always-read architecture sections (Agent Catalog, Principles), 3 layer invariants (STATUS_ constants, `record_agent_run`, no cross-feature imports); content derived from architecture doc, not hardcoded in profile
- `docs/learning-log.md` — new entry: API integration test coverage lesson (shallow happy-path tests miss critical failure modes; `/api-integration-tests` skill encodes the 9 categories as the guardrail)

D.4 pre-work complete (2026-05-13):
- `docs/adr/0011-recommendation-agent-input-contract.md` — ADR written
- `agent-architecture.md` — `GitHub Agent Query Contract` section added (API endpoints, filtering pipeline, exit conditions, guardrails); `GitHub Findings Schema` added under Agent-Specific Findings Schemas; walk anchor corrected: `?sha={release_sha}` walks backwards into the failing release, not forwards
- `agents/config.py` — 6 GitHub constants: `GITHUB_API_BASE`, `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_BRANCH`, `GITHUB_MAX_COMMITS`, `GITHUB_MSG_MAX_LEN`, `GITHUB_MAX_FILES_PER_COMMIT`; 9 new shared status constants: `STATUS_INVALID_INPUT`, `STATUS_UNAUTHENTICATED`, `STATUS_UNAUTHORIZED`, `STATUS_NOT_FOUND`, `STATUS_RATE_LIMITED`, `STATUS_SERVER_ERROR`, `STATUS_TIMEOUT`, `STATUS_NETWORK_ERROR`, `STATUS_SCHEMA_ERROR`
- `agents/specs/d4_github_extractor.md` — spec written and signed off; 21 TDD tests across 8 categories (happy path, input validation, auth, authz, not found, rate limiting, server/network failures, schema validation)

Frontend Sentry extractor coverage backfill complete (2026-05-13):
- `/api-integration-tests` skill created — 8-category test plan generator for any HTTP API integration; lives at `.claude/skills/api-integration-tests/skill.md`
- `agents/sentry_api.py` — `_validate_sentry_guardrails()` added (shared by all Sentry extractors); guards wrong types, negatives, bool-as-int
- `agents/frontend_sentry_extractor.py` — guardrail validation, schema check on `id` field, exception handling for KeyError/HTTPError/Timeout/ConnectionError all returning distinct statuses
- `agents/tests/test_frontend_sentry_extractor.py` — grew from 4 to 19 tests
- `agents/tests/test_sentry_api.py` — new file, 19 tests covering HTTP boundary layer
- 54/54 agent tests green

D.3 complete (2026-05-11):
- `agents/specs/d3_render_logs_extractor.md` — spec written and signed off
- `agents/patterns.py` — new shared module; `_INJECTION_RE`, `_EMAIL_RE`, `_PHONE_RE` moved from `sentry_api.py` (single home for all regex patterns)
- `agents/sentry_api.py` — updated to import from `patterns.py`
- `agents/render_logs_extractor.py` — implemented; filtering pipeline: drop deploy lines, injection check, level filter, deduplication, cap at `RENDER_MAX_DISTINCT_ERRORS`
- `agents/tests/test_render_logs_extractor.py` — 6 TDD tests green
- `agents/specs/DEPENDENCY_MAP.md` — `patterns.py` patterns added to shared utilities
- `agent-architecture.md` — `Render Logs Findings Schema` return shape reconciled with `Render Agent Query Contract`
- 25/25 agent tests green

A.6 complete (2026-05-11):
- `agents/config.py` — `RENDER_API_BASE`, `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_LOG_FETCH_LIMIT`, `RENDER_MAX_DISTINCT_ERRORS`, `RENDER_LOG_MAX_MSG_LEN` constants added
- `agent-architecture.md` — `Render Agent Query Contract` section added: endpoint, filtering pipeline, deduplication, guardrails, return shape

D.2 complete (2026-05-11):
- `agents/specs/d1_frontend_sentry_extractor.md` — retrospective spec written
- `agents/specs/d2_backend_sentry_extractor.md` — spec written and signed off
- `agents/sentry_api.py` — new shared module; 6 helpers extracted from D.1 (no cross-feature imports)
- `agents/backend_sentry_extractor.py` — implemented; `_get_status_code` adds `endpoint` + `status_code` fields
- `agents/tests/test_backend_sentry_extractor.py` — 5 TDD tests green
- `agents/config.py` — `STATUS_COMPLETED`, `STATUS_NO_DATA`, `STATUS_INJECTION_DETECTED` constants added
- `agents/sentry_api.py`, `agents/sentry_utils.py`, `agents/validator.py` — module-level purpose comments added
- `agents/CLAUDE.md` — spec-first rule added; cross-feature import guardrail in root `CLAUDE.md`
- 15/15 agent tests green

---

## Architecture Decisions — Resolved (2026-05-04)

All open architecture questions from the previous session are now resolved. The architecture doc has been updated to reflect all decisions below.

### Group 1 — Inter-Agent Data Contracts ✅

**Q1 — What does the Orchestrator pass to each extractor?** ✅ resolved
Guardrails only: `time_window`, `max_issues`, `max_frames`, `max_log_errors`, `max_commits`. Extractors receive no free-form instructions — they are bounded by the guardrail values and their own hardcoded project scope.

**Q2 — What does the Coding Agent receive?** ✅ resolved
The full combined structured payload from all extractors — not just interpretation summaries. The Orchestrator clubs all extractor dicts into one payload and passes it in a single call. Claude sees everything at once, enabling true cross-source correlation. Per-source limits (token budget targets) keep the combined payload under 3,000 input tokens.

**Q3 — Schema validation failure behaviour** ✅ resolved
Orchestrator stops routing entirely. Posts a comment on the GitHub Issue flagging the malformed finding. Does not silently pass invalid data downstream.

### Group 2 — Per-Agent Guardrails ✅

**Q4 — Should every extractor have its own query contract?** ✅ resolved
Yes — Sentry query contract is documented in the architecture doc. Render Logs, GitHub, and Codebase extractors will each get their own contract section when built (D.3–D.5). The Orchestrator is the single place that applies guardrails — extractors never self-widen.

### Group 3 — Token Efficiency Rules ✅

**Q5 — Trim-at-boundary as a universal principle** ✅ resolved
Elevated to Principle 9 in architecture doc. Applies to all extractors — raw API responses never reach the Orchestrator or Coding Agent.

**Q6 — Prompt caching strategy** ✅ resolved
Three components call the Anthropic SDK — Orchestrator, Diagnostic Agent, and Coding Agent. All three must use `build_system_prompt()` to wrap their system prompt with `cache_control`. System prompts do not change between runs so every subsequent call should hit the cache (~90% cheaper on input tokens). Pure Python extractors make zero Claude API calls so caching is not applicable to them.

**Q7 — Coding Agent payload — who strips?** ✅ resolved
The Orchestrator is responsible for the combined payload size. Each extractor already trims to minimum fields at its own boundary. The Orchestrator enforces the final combined token cap before passing to the Coding Agent — no further stripping inside Claude's context.

---

**Next: D.4 — GitHub Extractor**

Next: D.4 spec → sign-off → TDD → implement `agents/github_extractor.py`.
**Arch sections for D.4:** `Agent Catalog`, `Principles`, `Finding Schema`
**Note:** GitHub Agent Query Contract section does not exist yet — must be written in the architecture doc before the D.4 spec is finalised (same pattern as A.6 for Render).

`agents/backend_sentry_extractor.py` — pure Python extractor targeting `restaurant-backend` Sentry project. Same `run(guardrails: dict) -> dict` signature and escalating window ladder as D.1. Returns same fields as D.1 plus `endpoint` and `http_status`. Validate against Scenario 1 (reservation failures) and Scenario 3 (allergens).

**Path:** ~~B.2~~ ~~B.4~~ ~~B.5~~ ~~A.4~~ ~~D.1~~ ~~A.5~~ ~~DT-12~~ ~~D.1 smoke test~~ ~~DT-13~~ ~~DT-15~~ ~~DT-13 steps 13–14~~ ~~D.2~~ → D.3 → D.4 → D.5 → D.6 → E (orchestration)

**Deferred:** 8 pre-existing ESLint warnings (`react-refresh/only-export-components`) in shadcn/ui components — separate task, not blocking agents

---

## Time Window Strategy — Resolved (2026-05-04) ✅

**Decision:** Escalating window ladder controlled by the extractor, bounded by the Orchestrator's guardrails.

The extractor starts at the shortest window (`age:-1h`) and escalates only when zero issues are found. Once any issue is found, the window is locked — the extractor never widens further. The hard cap (`age:-24h`) is enforced by config, not by the Orchestrator at runtime.

```python
SENTRY_WINDOW_LADDER = ["age:-1h", "age:-6h", "age:-24h"]  # from config

def run(guardrails: dict) -> dict:
    for window in SENTRY_WINDOW_LADDER:
        issues = query_sentry_errors(window, guardrails["max_issues"])
        if issues:
            return extract_findings(issues, guardrails)
    return {"status": "no_data"}
```

- Extractor stays in control of its scope — Orchestrator passes `max_issues` and `max_frames`, not the window
- Ladder is configurable via `SENTRY_WINDOW_LADDER` in `agents/config.py` — never hardcoded
- All extractors adopt the same `run(guardrails: dict) -> dict` signature from D.2 onwards
- **DT-15 (complete):** `frontend_sentry_extractor.py` retrofitted with this signature and pure Python loop before D.2 — D.1 is now the reference implementation

---

## Session Progress (2026-05-11)

**Next: D.3 Render Logs Extractor.**

### A.6 — Render Logs Access ✅ (2026-05-11)
- `agents/config.py` — Render API constants added: `RENDER_API_BASE`, `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_LOG_FETCH_LIMIT`, `RENDER_MAX_DISTINCT_ERRORS`, `RENDER_LOG_MAX_MSG_LEN`
- `agent-architecture.md` — `Render Agent Query Contract` section added covering: API endpoint + params, log filtering pipeline, deduplication rules, injection/PII guards, return shape, exit conditions, guardrails table

### D.2 — Backend Sentry Extractor ✅ (2026-05-11)
- `agents/specs/d1_frontend_sentry_extractor.md` — retrospective spec written for D.1
- `agents/specs/d2_backend_sentry_extractor.md` — spec written; shared helpers moved to `sentry_api.py` (no cross-feature imports)
- `agents/sentry_api.py` — new shared module with 6 query helpers and guards; `frontend_sentry_extractor.py` refactored to import from here
- `agents/backend_sentry_extractor.py` — implemented; adds `endpoint` and `status_code` fields via `_get_status_code()`
- `agents/tests/test_backend_sentry_extractor.py` — 5 TDD tests; 15/15 total green
- `agents/config.py` — `STATUS_COMPLETED`, `STATUS_NO_DATA`, `STATUS_INJECTION_DETECTED` constants; hardcoded status strings removed from both extractors
- `agents/CLAUDE.md` — spec-first rule enforced for all new agents/extractors
- Root `CLAUDE.md` — cross-feature import guardrail added; cross-document traceability rules added; `design-plan` skill created
- `docs/learning-log.md` — two new entries: cross-feature imports, pair programming violation

### DT-13 steps 13–14 ✅ (2026-05-09)
- `agents/frontend_sentry_extractor.py` — `run()` signature updated to `run(guardrails: dict, issue_number: str = "") -> dict`; `issue_number` forwarded to all 3 `record_agent_run` call sites
- `agents/specs/DEPENDENCY_MAP.md` — `record_agent_run` row updated to 4-param signature; `run()` contract pattern updated to match
- 10/10 agent tests green, no regressions

---

## Session Progress (2026-05-07)

**Next: Complete DT-13 steps 13–14, then D.2.**

### DT-13 steps 11–12 ✅ (2026-05-07)
- `agents/sentry_utils.py` — `issue_number: str = ""` added to `record_agent_run` signature; written to `tags["issue_number"]`; `cache_read_input_tokens` and `cache_creation_input_tokens` summed and added to `extra`; raw `usage_by_turn` list preserved in `extra`
- `agents/tests/test_sentry_utils.py` — 2 new tests green: `test_record_agent_run_issue_number_tag`, `test_record_agent_run_usage_by_turn_preserved`; 6/6 passing
- DT-14 merged into DT-13 — was redundant; `agents/specs/dt14_observability_contract.md` deleted; all remaining work tracked in `agents/specs/dt13_agent_observability.md` steps 13–15

### Slice rules and dependency maps ✅ (2026-05-07)
- Root `CLAUDE.md` — generic slice rule added: every layer has a dependency map; check before, update after
- `backend/CLAUDE.md` — pointer to `backend/specs/DEPENDENCY_MAP.md`
- `agents/CLAUDE.md` — pointer to `agents/specs/DEPENDENCY_MAP.md`
- `agents/specs/DEPENDENCY_MAP.md` — created; captures all existing signatures: `record_agent_run`, `build_system_prompt`, `validate_finding`, all D.1 Sentry functions, `run()` contract pattern, config constants

### Previous session — Architecture doc audit ✅
- DT-14 rewritten — now covers all three gaps (merged into DT-13)
- Architecture doc updated — Backend Sentry return dict, `record_agent_run` signature, `usage_by_turn` table row
- Current Focus updated — DT-15 done, DT-13 steps 11–12 next

---

## Session Progress (2026-05-03)

**DT-13 complete. Next: D.2 Backend Sentry Extractor.**

### DT-13 — Agent Observability via Sentry ✅ complete (2026-05-03), updated 2026-05-05
- `agents/sentry_utils.py` — `record_agent_run(agent_name, result: dict, usage_by_turn)` uses `capture_event` (not `start_transaction` — Performance tab requires paid plan); signature updated from `result_yaml: str` to `result: dict` after DT-15
- `agents/config.py` — `AGENTS_SENTRY_DSN` added (empty default = opt-in locally)
- `agents/requirements.txt` — `sentry-sdk==2.58.0` + `certifi` + `urllib3` pinned
- `agents/tests/test_sentry_utils.py` — 4 TDD tests green; pass dicts not YAML strings
- `agents/tests/test_frontend_sentry_extractor.py` — `record_agent_run` mocked to prevent real Sentry calls
- `agents/CLAUDE.md` — observability guardrail + token efficiency rules + wiring checklist

**DT-13 gaps identified (2026-05-04 / 2026-05-07):**

`usage_by_turn` currently captures only `input_tokens` and `output_tokens`. Three additions are needed — tracked as **DT-14** below:

1. **Cache token fields** — `cache_read_input_tokens` and `cache_creation_input_tokens` missing; cache reads cost 10% of normal rate and skew the total without them
2. **`issue_number` tag** — no correlation ID today; without it, Sentry cannot group all agents from one investigation together; pass GitHub Issue number from Orchestrator → each agent's `run()` → `record_agent_run`
3. **`usage_by_turn` in extra** — raw per-turn list is currently summed away; preserving it in the Sentry event `extra` enables drill-down to diagnose token growth across turns

---

### DT-15 — Refactor D.1 to Pure Python Extractor ✅ complete (2026-05-05)

- Removed `import anthropic`, `build_system_prompt`, `TOOLS`, `SYSTEM_PROMPT`, `FINDING_YAML_TEMPLATE`
- Replaced `run()` agentic loop with pure Python escalating window ladder (`SENTRY_WINDOW_LADDER`)
- Signature: `run(guardrails: dict) -> dict` — structured dict, not YAML string
- Removed `FRONTEND_SENTRY_MAX_TURNS`, `FRONTEND_SENTRY_MAX_TOKENS`, `FRONTEND_SENTRY_MODEL` from `config.py`
- Added `SENTRY_WINDOW_LADDER`, `SENTRY_STACK_FRAME_LIMIT` to `config.py`
- 4 tests green: happy path, window escalation, no_data, injection detection
- D.1 is now the reference implementation for D.2–D.4

---

### DT-14 — Merged into DT-13 ✅ (2026-05-07)

DT-14 was redundant — all three gaps were already tracked as steps 11–15 in the DT-13 spec. Merged and `dt14_observability_contract.md` deleted. See `agents/specs/dt13_agent_observability.md` for remaining steps 13–15.

---

## Session Progress (2026-05-02)

**D.1 smoke test complete. DT-13 spec written and signed off.**

### D.1 production smoke test — ✅ complete (2026-05-02)
Real Sentry finding returned: `EADDRINUSE :::4000` in `graphql-gateway/index.ts`. All 4 checks passed: tool called turn 1, valid YAML shape, `status: completed`, `pii_flag: false`. Cost: $0.02 (Haiku, ~3 turns) — baseline for DT-13 budget constants.

### DT-13 spec — ✅ signed off (2026-05-02)
`agents/specs/dt13_agent_observability.md` written. Key design:
- `agents/sentry_utils.py` — `record_agent_run(agent_name, result_yaml, usage_by_turn)` wraps each run in a Sentry Performance transaction
- Measurements: `input_tokens`, `output_tokens`, `total_tokens`, `turns_used`, `confidence_numeric` (high=3, medium=2, low=1)
- Tags: `agent`, `release` (Git SHA)
- Transaction status: `ok` for completed, `deadline_exceeded` for partial
- `AGENTS_SENTRY_DSN` empty string = opt-in; never breaks local dev without DSN
- Sentry dashboard: token trend, confidence by agent, partial run rate

### A.5 — Runbook ✅
`docs/runbooks/troubleshooting.md` — 5 patterns: `reservation-validation-spike`, `render-cold-start-503`, `missing-field-frontend-query`, `seed-data-price-error`, `graphql-schema-resolver-drift`. Each has Symptoms, Likely cause, Investigation steps, Escalation criteria.

### DT-12 — Per-project env restructuring ✅
`agents/.env.example`, `backend/.env.example`, `graphql-gateway/.env.example` — each sub-project owns its own env file. Root `.env.example` trimmed to frontend-only vars. `agents/config.py` loads `agents/.env` via `load_dotenv(override=False)`.

**D.1 complete.** `agents/frontend_sentry_extractor.py` fully implemented and test green. Next: A.5 runbook.

### D.1 — Frontend Sentry Agent ✅
`agents/frontend_sentry_extractor.py` — complete:
- `query_sentry_errors(project_slug)` — GET `/projects/{org}/{slug}/issues/` with `is:unresolved` filter, limit 25
- `get_stack_trace(issue_id)` — GET `/issues/{id}/events/latest/`
- `get_affected_releases(issue_id)` — GET `/issues/{id}/tags/release/`, extracts `topValues[].value` list
- `TOOLS` — Anthropic SDK JSON Schema definitions for all 3 functions
- `SYSTEM_PROMPT` — read-only observability persona; PII/injection guard rules; YAML shape from `FINDING_YAML_TEMPLATE`; wrapped with `build_system_prompt()` for prompt caching
- `run()` — bounded agentic loop (`FRONTEND_SENTRY_MAX_TURNS`); appends assistant messages and tool results each turn; returns YAML string on `end_turn`; returns `status: partial` fallback if turn budget exhausted
- TDD test green: `test_frontend_sentry_identifies_schema_drift` — mocks 2-turn conversation (tool_use → end_turn); asserts 10 fields in parsed YAML output

---

## Session Progress (2026-05-01)

**A.4 complete. D.1 started (TDD red phase confirmed).**

### A.4 — Test scenarios file ✅
`docs/agent-test-scenarios.md` written. Covers all 5 scenarios (reservation failures, Render cold start, missing allergens, wrong order total, schema drift). Each scenario defines: bug introduction steps, trigger, expected agent routing, expected findings YAML per agent, expected recommendation output, and cleanup. File serves as acceptance criteria for all Phase D agents.

### `agents/config.py` extended
- `SENTRY_API_BASE` — env var with default `https://sentry.io/api/0`; extracted from agent code per "config over hardcoding" rule
- `AGENT_MAX_TURNS` / `AGENT_MAX_TOKENS_PER_TURN` — global defaults (5 turns, 1024 tokens)
- Per-agent overrides for all 6 agents; all fall back to global defaults except: `DIAGNOSTIC_MAX_TURNS` defaults to `8` (deeper tracing), `CODING_MAX_TURNS` defaults to `1` (no tools, one turn only)

### `agents/requirements.txt` updated
Added `pytest==9.0.3` and its 5 transitive dependencies (colorama, iniconfig, packaging, pluggy, pygments) — all pinned.

### D.1 TDD test written — red phase confirmed
- `agents/tests/__init__.py` — empty; required so pytest resolves `from agents.frontend_sentry_extractor import run` correctly when run from repo root
- `agents/tests/test_frontend_sentry_extractor.py` — acceptance test for Scenario 5 (schema drift: `preparation_time` field in frontend query but missing from gateway schema)
  - `SENTRY_EVENT` — mock Sentry issue dict with TypeError on `useMenu.ts`
  - `EXPECTED_FINDING` — expected agent output: `agent=frontend-sentry`, `confidence=high`, `affected_layer=gateway`, `regression=True`, `affected_field=preparation_time`
  - `test_frontend_sentry_identifies_schema_drift()` — patches `query_sentry_errors`, calls `run()`, asserts 10 specific fields
  - **Red phase confirmed:** `AttributeError: module 'agents' has no attribute 'frontend_sentry_extractor'` — module does not exist yet

### D.1 agent file started — 3 of 4 parts written
`agents/frontend_sentry_extractor.py` — in progress:
- Imports: `os`, `requests`, `FRONTEND_SENTRY_MAX_TURNS`, `FRONTEND_SENTRY_MAX_TOKENS`, `SENTRY_API_BASE` from config
- `query_sentry_errors(project_slug)` — GET `/projects/{org}/{slug}/issues/` with `is:unresolved` filter, limit 25
- `get_stack_trace(issue_id)` — GET `/issues/{id}/events/latest/`
- `get_affected_releases(issue_id)` — GET `/issues/{id}/tags/release/`, extracts `topValues[].value` list
- **Still to write:** `TOOLS` list (Anthropic SDK tool definitions), system prompt using `build_system_prompt`, `run()` agentic loop

### New reference doc committed
`docs/engineering-practices/mcp-vs-agents.md` — committed on branch `docs/mcp-vs-agents`. Covers MCP vs SDK agent pattern decision, architecture diagrams, sequence diagrams, agentic loop flowchart, decision guide, and rationale for every agent in this project.

Run tests from repo root with agents venv activated:
```
source agents/.venv/Scripts/activate
python -m pytest agents/tests/ -v
```

## Session Progress (2026-04-30)

**Phase B — fully complete.** All five foundation tasks done and merged to main.

Files created:
- `agents/schemas/models.py` — Pydantic models: `TimeWindow`, `Metadata`, `Interpretation`, `BaseFinding`, `FrontendSentryData`, `FrontendSentryFinding`; Literal type constants (`AgentName`, `AgentStatus`, `ConfidenceLevel`, `AffectedLayer`) defined outside classes for reuse
- `agents/schemas/__init__.py` — makes `schemas/` a Python package
- `agents/schemas/finding-schema.json` — auto-generated from models via `FrontendSentryFinding.model_json_schema()`; regenerate with `python -c "import json; from schemas.models import FrontendSentryFinding; open('schemas/finding-schema.json','w').write(json.dumps(FrontendSentryFinding.model_json_schema(), indent=2))"`
- `agents/validator.py` — single function `validate_finding(yaml_str: str) -> dict`; extracts YAML block from agent comment, parses with `yaml.safe_load`, validates against `finding-schema.json` using `jsonschema`
- `agents/config.py` — 7 model constants (`ORCHESTRATOR_MODEL`, `CODING_MODEL`, `DIAGNOSTIC_MODEL`, `FRONTEND_SENTRY_MODEL`, `BACKEND_SENTRY_MODEL`, `RENDER_LOGS_MODEL`, `GITHUB_MODEL`) read from env vars; defaults: Sonnet 4.6 for Orchestrator/Recommendation/Codebase, Haiku 4.5 for Sentry/Render/GitHub
- `agents/prompt_utils.py` — single function `build_system_prompt(text: str) -> list[dict]`; wraps system prompt text in Anthropic SDK cache_control block; all agents must use this when building their system prompt

`agents/requirements.txt` updated with: `pydantic==2.13.3`, `pyyaml==6.0.3` (jsonschema was already present from B.1).

`.venv` is inside `agents/` — activate with `source .venv/Scripts/activate` (bash on Windows) before running any Python commands.

---

## Guiding Principles

- Build one phase at a time; validate it fully before moving to the next.
- Test scenarios (`docs/agent-test-scenarios.md`) are the acceptance criteria — an agent is not done until it passes its relevant scenarios.
- Runbook must be updated before each agent is built — agents read the runbook, not the other way around.
- No agent writes to external systems until the orchestration layer is complete and authorization logic is in place.
- D.1–D.4 extractors (Sentry, Render, GitHub) are pure Python — zero Claude API calls. D.5 (Diagnostic Agent) uses Claude for navigation only — read-only filesystem, no write access anywhere. D.6 (Coding Agent) uses Claude to generate a targeted code patch — writes to local filesystem (fix_files[0] only), commits via local git (pre-commit hooks fire), pushes branch, opens draft PR via GitHub API; optional pipeline stage. No Claude Code sub-agents anywhere.

---

## Phase A — Prerequisites

> Must be complete before any agent is built. Agents are only as good as their signal quality.

| # | Task | Description | Status |
|---|---|---|---|
| A.1 | Backend Sentry | Install `sentry-sdk[fastapi]` on backend; wire to FastAPI; tag releases with commit SHA so errors map to deployments | ✅ Done — `SENTRY_DSN` and `GIT_COMMIT_SHA=$RENDER_GIT_COMMIT` confirmed set in Render |
| A.2 | Sentry release tagging in CI | Separate `sentry-release.yml` workflow fires on push to main; tags release with Git SHA via `getsentry/action-release@v1` | ✅ Done — extended to create releases for all three Sentry projects (`restaurant-backend`, `restaurant-frontend`, `restaurant-gateway`) using the same commit SHA so agents can correlate errors across projects. **Validated 2026-04-30:** all three Sentry projects show release `cfe6747` matching merge commit `cfe6747637e4` on main |
| A.3 | Frontend Sentry + Gateway Sentry | Wire React frontend and GraphQL gateway to their own Sentry projects; all three layers (backend, frontend, gateway) must be on separate projects with release tagging so agents can query each independently | ✅ Done — **(1)** `SENTRY_DSN`, `VITE_SENTRY_DSN`, `GATEWAY_SENTRY_DSN` added to `.env.example`; **(2)** `release: import.meta.env.VITE_SENTRY_RELEASE` added to `main.tsx`; **(3)** `VITE_SENTRY_RELEASE=$VERCEL_GIT_COMMIT_SHA` set in Vercel for frontend; **(4)** gateway updated to read `GATEWAY_SENTRY_DSN` and `GATEWAY_SENTRY_RELEASE` in both `index.ts` and `api/graphql.ts`; **(5)** `GATEWAY_SENTRY_DSN` and `GATEWAY_SENTRY_RELEASE=$VERCEL_GIT_COMMIT_SHA` set in Vercel for gateway; new `restaurant-gateway` Sentry project created. **Next remaining step:** trigger a test error in each layer post-D.1 to confirm errors link to release SHA in Sentry |
| A.4 | Test scenarios file | Write `docs/agent-test-scenarios.md` — 5 real bugs introduced one at a time to production; each scenario defines trigger, expected agent routing, expected findings per agent, expected recommendation | ✅ Done — all 5 scenarios written (reservation validation spike, Render cold start, missing allergens, seed data price error, schema drift); file is the acceptance criteria for all Phase D agents |
| A.5 | Runbook coverage | Create `docs/runbooks/troubleshooting.md` — cover all 5 test scenarios with named pattern, investigation steps, and expected findings | ✅ Done — all 5 patterns written (reservation-validation-spike, render-cold-start-503, missing-field-frontend-query, seed-data-price-error, graphql-schema-resolver-drift); no expected findings section (belongs in test scenarios, not runbook) |
| A.6 | Render logs access | Confirm Render API key is available as env variable; document which log endpoints the Render Logs Agent will call | ✅ Done — `RENDER_API_KEY` and `RENDER_SERVICE_ID` confirmed in `agents/.env.example`; `RENDER_LOG_FETCH_LIMIT`, `RENDER_MAX_DISTINCT_ERRORS`, `RENDER_LOG_MAX_MSG_LEN` added to `agents/config.py`; **Arch sections:** `Render Agent Query Contract` in `agent-architecture.md` — documents endpoint, filtering pipeline, deduplication, guardrails, and return shape |
| A.7 | Sequence diagram | Add sequence diagram to agent architecture doc showing agent transitive dependencies and Sentry release → error correlation flow | ✅ Done — release ID end-to-end flow diagram and both orchestration flow diagrams added to `agent-architecture.md` under Monitoring Workflows and Orchestration Flow sections |

---

## Phase B — Agent Package Foundation

> Establish the `agents/` Python package and shared infrastructure before any individual agent is built. Every subsequent phase depends on this.

| # | Task | Description | Status |
|---|---|---|---|
| B.1 | `agents/` package setup | Create `agents/` directory at repo root; add `requirements.txt` with `anthropic`, `jsonschema`, `PyGithub`, `requests` pinned to exact versions; `.venv` added to `.gitignore` | ✅ Done — `agents/__init__.py`, `agents/requirements.txt` (pinned versions), `agents/.venv` gitignored; merged via PR #52 `feat/agents-package` |
| B.2 | Finding schema — Pydantic models | Create `agents/schemas/models.py` — `BaseFinding` Pydantic model defines three sections: `metadata` (common envelope), `findings` (agent-observed data), `interpretation` (agent conclusion for Coding Agent). Agent-specific subclasses (e.g. `FrontendSentryFinding`) extend `BaseFinding` with their own `findings` fields. Generate `agents/schemas/finding-schema.json` from models via `pydantic.model_json_schema()` — never hand-edit the JSON file. **Pydantic is the single source of truth; JSON Schema file is auto-generated.** See architecture doc Finding Schema section for field definitions and rationale. Sentry agent subclasses must declare one of three release ID states in metadata: `release_id: "sha"` (present), `release_id: null` (fallback to timestamp, Coding Agent downgrades confidence to medium), `release_id_unresolvable: true` (SHA in Sentry but not in git history) | ✅ Done — `agents/schemas/models.py` with `BaseFinding`, `FrontendSentryFinding`; `agents/schemas/finding-schema.json` auto-generated; `pydantic==2.13.3` added to `requirements.txt`; merged via `feat/finding-schema-models` |
| B.3 | Schema validator utility | Write `agents/validator.py` — single function `validate_finding(yaml_str)` that parses the YAML block from an agent comment and validates it against `agents/schemas/finding-schema.json` using `jsonschema`; raise a descriptive error on failure. The JSON Schema file must be regenerated from `models.py` before running the validator if models changed | ✅ Done — `agents/validator.py` with `validate_finding(yaml_str)`; `pyyaml==6.0.3` added to `requirements.txt`; merged via `feat/finding-schema-validator` |
| B.4 | Model config | Add `agents/config.py` — reads per-agent model names from environment variables with defaults (Sonnet 4.6 for Orchestrator, Recommendation, Codebase; Haiku 4.5 for Sentry, Render, GitHub agents); never hardcode model IDs | ✅ Done — `agents/config.py` with 7 model constants read from env vars; merged via `feat/agent-model-config` |
| B.5 | Prompt caching | Add `cache_control: {"type": "ephemeral"}` to the last static block of every agent's system prompt so the Anthropic SDK caches it across runs; verify cache hits appear in `usage.cache_read_input_tokens` in the response; required for all agents — system prompts do not change between investigations so every run should hit the cache | ✅ Done — `agents/prompt_utils.py` with `build_system_prompt(text)`; merged via `feat/prompt-caching-utility` |

---

## Phase C — Monitoring Workflows

> Build the outer monitoring layer — two GitHub Actions cron workflows that poll Sentry and create GitHub Issues. No Claude or agent code is involved in this phase. The orchestrator is triggered only after these workflows create an issue.

| # | Task | Description | Status |
|---|---|---|---|
| C.1 | `sentry-monitor-backend.yml` | Scheduled workflow (every 30 min, configurable via env var); calls Sentry backend project API; checks error count against configurable threshold; de-duplication check (query open issues for matching Sentry group ID); if no match → create GitHub issue with labels `needs-analysis` + `source:backend-sentry`; if match → comment on existing issue with updated count and timestamp | ⏳ Pending |
| C.2 | `sentry-monitor-frontend.yml` | Same as C.1 for the frontend Sentry project; creates issues with `needs-analysis` + `source:frontend-sentry` labels | ⏳ Pending |
| C.3 | `agent-orchestrator.yml` | Triggered `on: issues: [labeled: needs-analysis]`; requires both `needs-analysis` and a `source:*` label to be present; runs `python agents/orchestrator.py --issue ${{ github.event.issue.number }}`; passes `ANTHROPIC_API_KEY`, Sentry tokens, Render API key, GitHub token as secrets | ⏳ Pending |
| C.4 | Issue body contract | Define and document the exact issue body template the monitoring workflows must write: Sentry group ID (fingerprint), error count, first/last seen timestamps, top-line error message (PII-redacted), Sentry deep link | ⏳ Pending |

---

## Phase D — Individual Agents

> Build and validate each agent in isolation. Every agent slice has two steps: (1) implement + unit tests green; (2) Phase 2 stub test — real API call, manual, human decision.
> **Test strategy reference:** `docs/engineering-practices/agent-architecture.md` — Test Strategy section.

| # | Task | Description | Status |
|---|---|---|---|
| D.1 | Frontend Sentry Extractor | `agents/frontend_sentry_extractor.py` — pure Python escalating window loop; `run(guardrails: dict) -> dict`; `query_sentry_errors`, `get_stack_trace`, `get_affected_releases` (frontend project only); zero Claude API calls; injection + PII detection; 4 tests green | ✅ Done (DT-15 refactor complete 2026-05-05) |
| D.2 | Backend Sentry Extractor | `agents/backend_sentry_extractor.py` — pure Python extractor; zero Claude API calls; `run(guardrails: dict) -> dict`; escalating window ladder; same fields as D.1 plus `endpoint` and `http_status`; validate against Scenario 1 (reservation failures) and Scenario 3 (allergens) | ⏳ Pending |
| D.3 | Render Logs Extractor | `agents/render_logs_extractor.py` — pure Python extractor; zero Claude API calls; fetches Render log lines, filters to error/warn, deduplicates by message, caps at 10 distinct errors; `run(guardrails: dict) -> dict`; validate against Scenario 2 (cold start) | ✅ Done |
| D.4 | GitHub Extractor | `agents/github_extractor.py` — pure Python extractor; zero Claude API calls; fetches commits and PR metadata for a given release SHA; `run(guardrails: dict) -> dict`; validate against Scenario 3 (allergens issue) and Scenario 4 (wrong total) | ⏳ Pending |
| D.5 | Diagnostic Agent | `agents/diagnostic_agent.py` — Claude-assisted navigator; read-only filesystem access scoped to `src/`, `graphql-gateway/`, `backend/`, `docs/`; zero GitHub access; uses Claude to navigate multi-hop code traces (crash line → symbol → source → root cause location); returns structured findings ~50 tokens — crash location, root cause file/line, missing field, fix type, runbook match; never passes raw code snippets to Coding Agent; `run(guardrails: dict) -> dict` | ✅ Done |
| D.6 | Coding Agent | `agents/coding_agent.py` — optional pipeline stage (Orchestrator `enable_coding_agent` flag); receives combined payload including D.5 diagnostic findings (`fix_files`, `fix_type`, `fix_detail`, `fix_location`); reads local file content, makes one Claude call to generate `original_snippet` + `replacement_snippet`; verifies snippet exists verbatim (hallucination guard); commits via local `git commit` (pre-commit hooks fire) + `git push`; opens draft PR via single GitHub API call; auto-commits `fix_files[0]` only — `fix_files[1:]` listed in PR description; requires git-enabled environment (repo checked out, pre-commit installed, GITHUB_TOKEN set); 41 TDD tests planned; spec: `agents/specs/d6_recommendation_agent.md` | ⏳ Pending |

### Phase 2 — Agent Stub Tests (Manual, run after each agent above is implemented)

> Real API calls. Human decision — costs money for Claude-calling agents. Run once per agent after unit tests are green. See Test Strategy in architecture doc for test data preparation steps per agent.

| # | Task | Real calls | Test data needed | Status |
|---|---|---|---|---|
| D.ST.1 | Frontend Sentry stub test | Real Sentry API | At least one unresolved frontend error in Sentry (introduce Scenario 3 allergens bug) | ⏳ Pending |
| D.ST.2 | Backend Sentry stub test | Real Sentry API | At least one unresolved backend error in Sentry (introduce Scenario 1 reservation bug) | ⏳ Pending |
| D.ST.3 | Render Logs stub test | Real Render API | Any backend 500 or cold start 503 in Render logs | ⏳ Pending |
| D.ST.4 | GitHub Extractor stub test | Real GitHub API | Any recent commit on `main`; use HEAD as `release_sha` | ⏳ Pending |
| D.ST.5 | Diagnostic Agent live smoke test | Real Anthropic SDK | See steps below — introduces a known bug, captures Sentry crash_location, runs agent, verifies recommendation | ✅ Done |
| D.ST.5a | Diagnostic Agent token budget analysis | Real Anthropic SDK | Instrument a clean run to capture `usage_by_turn` per-turn; understand exactly why the failed run hit 11k input tokens; calibrate `DIAGNOSTIC_MAX_FILE_CHARS` and guardrail defaults; update spec token budget target | ✅ Done |

> **Decision made (2026-05-18):** Option A (stub trim after each Claude response) chosen for D.ST.5a. Option B (line-range reads) deferred — revisit after Option A is stabilised. Option C (pre-read / single-turn) deferred. See Appendix in `agents/specs/d5_diagnostic_agent.md` for full rationale.
| D.ST.6 | Coding Agent stub test | Real Anthropic SDK | Hand-assembled findings dict from D.ST.1–D.ST.5 real outputs | ⏳ Pending |

### D.ST.5 — Detailed Steps (Diagnostic Agent Live Smoke Test)

**Bug to introduce:** Remove `allergens` from the GraphQL query in `src/hooks/useMenu.ts`.
This is Scenario 3 — safest choice, frontend-only change, no database or backend touched, easy to revert.
The existing Sentry exercise (task 3.16.15) already used this bug, so the pattern is known.

**Step 1 — Introduce the bug**
- In `src/hooks/useMenu.ts`, remove `allergens` from the GraphQL query fields
- Deploy to Vercel (or run the frontend locally against the deployed backend)
- Trigger a page load that calls the menu query

**Step 2 — Confirm Sentry captured the error**
- Open the Sentry frontend project
- Find the new error — it will reference `useMenu.ts` or the component consuming the hook
- Note the exact `crash_location`: file path + line number (e.g. `src/hooks/useMenu.ts:42`)
- Note the Sentry issue ID

**Step 3 — Run the Diagnostic Agent**
```python
# run from repo root — real Anthropic SDK call, costs tokens
import agents.diagnostic_agent as agent

guardrails = {
    "crash_location": "src/hooks/useMenu.ts:42",  # replace with real line from Sentry
    "changed_files": ["src/hooks/useMenu.ts"],
    "max_files_to_read": 3,  # keep low — file contents accumulate in context each turn
}
result = agent.run(guardrails, issue_number="smoke-test-1")
print(result)
```

**Step 4 — Verify the result**
- `result["status"]` == `"completed"`
- `result["root_cause_file"]` points to the correct file (useMenu.ts or the GraphQL query file)
- `result["fix_type"]` == `"remove_field"` or `"add_field"` (field was removed from query)
- `result["fix_detail"]` describes adding `allergens` back
- `usage_by_turn` logged to Sentry — check token count is under 5k total

**Step 5 — Revert the bug**
- Add `allergens` back to the GraphQL query in `src/hooks/useMenu.ts`
- Deploy or restart — confirm no Sentry errors

**Pass criteria:** `status: completed`, `root_cause_file` correct, `fix_detail` actionable, token usage reasonable. D.6 does not start until this passes.

---

## Phase E — Orchestration Layer

> Wire agents together under `orchestrator.py`. Add trigger handling, schema validation, routing logic, and authorization gating.

| # | Task | Description | Status |
|---|---|---|---|
| E.1 | Orchestrator design | Document routing logic for each of the three trigger types (monitoring workflow label event, manual GitHub issue, `/troubleshoot` skill) — which agents are invoked, in what order, under what conditions; confirm no direct Sentry webhook triggers (not used — paid feature) | ⏳ Pending |
| E.2 | Orchestrator implementation | `agents/orchestrator.py --issue <number>` — reads issue body and labels; routes to the correct Sentry agent based on `source:*` label; invokes Render Logs, Codebase, GitHub agents; validates each finding via `agents/validator.py` before routing (malformed finding → flag on issue, stop); passes validated findings to Coding Agent. **Note:** Coding Agent currently runs `pytest agents/tests/ -q` (workaround for split venvs). Production fix: dispatch Coding Agent inside the target layer's pipeline (backend/frontend/agents each has its own venv + test runner); `_get_test_command(fix_files[0])` derives the right command from the path prefix — design this as part of E.2. | ⏳ Pending |
| E.3 | `/troubleshoot` skill | Claude Code skill in `.claude/skills/`; accepts symptom description or GitHub issue number; shell wrapper that calls `python agents/orchestrator.py --issue <number>`; same entry point as automated path | ⏳ Pending |
| E.4 | GitHub write authorization | Coding Agent always has `open_draft_pr` in its tool list — no `/approve` gate before PR creation (draft PRs cannot be merged without human action on GitHub). Orchestrator always has `post_github_comment` and `send_email`. No agent ever has `merge_pr` — merging happens through the normal GitHub UI by a human. Compliance flag (`pii_flag: true` in any finding) adds a compliance notice to the GitHub Issue and PR description — human must acknowledge before merging | ⏳ Pending |
| E.5 | Confidence-gated notifications | Orchestrator reads `confidence` from Coding Agent finding; high → post GitHub comment + send Resend email; medium → post GitHub comment only; low → post GitHub comment only with "investigation inconclusive" framing | ⏳ Pending |
| E.6 | Timeout and escalation | Orchestrator checks for human response after 24 hours on high-confidence findings → send reminder email; after 48 hours → add `escalation-needed` label; never act autonomously on timeout — only re-notify | ⏳ Pending |

---

## Phase EV — Integration Touch Points (Manual, after Phase E)

> Test only the direct connections between the Orchestrator and each agent it calls. Agents that do not call each other are not cross-tested. Real API calls — human decision.
> **Test data:** Use Scenario 3 (missing allergens) as the baseline — no database change required, safest to introduce and revert.

| # | Task | Connection tested | What to verify | Status |
|---|---|---|---|---|
| EV.1 | Orchestrator → Frontend Sentry | Guardrails shape + status routing | Orchestrator passes correctly shaped guardrails; agent returns `completed`; Orchestrator parses status without error | ⏳ Pending |
| EV.2 | Orchestrator → Backend Sentry | Guardrails shape + status routing | Same as EV.1 for backend project slug | ⏳ Pending |
| EV.3 | Orchestrator → Render Logs | Guardrails shape + status routing | Same as EV.1 for Render API | ⏳ Pending |
| EV.4 | Orchestrator → GitHub Extractor | Guardrails shape + status routing | Orchestrator passes `release_sha` correctly; agent returns `completed` with commits list | ⏳ Pending |
| EV.5 | Orchestrator → Diagnostic Agent | Guardrails assembled from prior findings | Orchestrator correctly maps `crash_location` from Sentry finding into Codebase guardrails; agent returns `completed` | ⏳ Pending |
| EV.6 | Orchestrator → Coding Agent | Combined findings payload | Orchestrator correctly assembles all agent findings into one payload; Coding Agent returns `completed` with interpretation | ⏳ Pending |

**Test data preparation before running EV.1–EV.6:**
1. Introduce the Scenario 3 allergens bug (`docs/agent-test-scenarios.md`) and deploy
2. Confirm Sentry frontend project shows at least one error for the allergens issue
3. Note the Sentry issue ID
4. Confirm GitHub `main` has at least one recent commit
5. Create a GitHub issue on the repo with the Orchestrator trigger format

---

## Phase F — Validation

> Run the complete agent stack end-to-end against all five test scenarios.

| # | Task | Description | Status |
|---|---|---|---|
| F.1 | Scenario 1 — Reservation failures | Trigger: monitoring workflow creates issue; backend Sentry agent detects spiking validation errors; codebase agent traces to date limit rule; recommendation agent recommends fix | ⏳ Pending |
| F.2 | Scenario 2 — Render cold start | Trigger: monitoring workflow creates issue; Render logs agent correlates Sentry 503s with startup log; codebase agent rules out code bug; recommendation agent recommends keep-alive or tier upgrade | ⏳ Pending |
| F.3 | Scenario 3 — Missing allergens | Trigger: GitHub issue opened manually (or via `/troubleshoot`); codebase agent traces null field from frontend → query → schema → resolver → backend; recommendation agent recommends adding field back to query | ⏳ Pending |
| F.4 | Scenario 4 — Wrong order total | Trigger: GitHub issue opened; codebase agent traces total → mutation input → menu query → seed data; GitHub agent finds recent commit touching price; recommendation agent identifies price entry error | ⏳ Pending |
| F.5 | Scenario 5 — Schema drift | Trigger: monitoring workflow creates issue from Sentry alert; codebase agent detects undefined field in order confirmation; traces to resolver/schema gap; recommendation agent recommends running validate-schema.js | ⏳ Pending |
| F.6 | False positive check | Run monitoring workflow against a clean system with no active issues; confirm no issue is created and no agent is invoked | ⏳ Pending |
| F.7 | Prompt injection check | Introduce a synthetic Sentry error with an injection payload in the message; confirm agent sets `injection_flag: true`, stops processing the source, and orchestrator opens a `security-incident` flagged issue | ⏳ Pending |

---

## Dependencies

```
A.1 (backend Sentry) ──────────────────────────────→ D.2 (Backend Sentry Agent)
A.2 (release tagging) ─────────────────────────────→ D.2 (errors map to deployments)
A.3 (frontend Sentry) ─────────────────────────────→ D.1 (Frontend Sentry Agent)
A.4 (test scenarios) ──────────────────────────────→ D.1–D.6 (acceptance criteria)
A.5 (runbook) ─────────────────────────────────────→ D.5 (Diagnostic Agent reads runbook)
A.6 (Render API) ──────────────────────────────────→ D.3 (Render Logs Agent)

B.1 (agents/ package) ─────────────────────────────→ B.2, B.3, B.4, B.5, all of D and E
B.2 (finding schema) ──────────────────────────────→ B.3 (validator), D.1–D.6 (agents conform to schema)
B.3 (schema validator) ────────────────────────────→ E.2 (orchestrator validates before routing)
B.4 (model config) ────────────────────────────────→ D.1–D.6, E.2
B.5 (prompt caching) ──────────────────────────────→ D.5, D.6, E.2 only (Claude callers only — D.1–D.4 are pure Python extractors with zero Claude calls)

C.1 (backend monitor workflow) ────────────────────→ C.3 (orchestrator triggered by label)
C.2 (frontend monitor workflow) ───────────────────→ C.3 (orchestrator triggered by label)
C.3 (agent-orchestrator.yml) ──────────────────────→ E.2 (entry point for automated path)

D.1–D.6 (all agents) ──────────────────────────────→ E.2 (Orchestrator invokes them)
E.2 (Orchestrator) ────────────────────────────────→ E.3, E.4, E.5, E.6
E.2–E.6 (full orchestration) ──────────────────────→ F.1–F.7
```
