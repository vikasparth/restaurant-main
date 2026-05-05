# Agent Implementation Execution Plan — Aap ki Rasoi

**Status: IN PROGRESS**
**Last updated: 2026-05-04**
**Reference:** See `docs/engineering-practices/agent-architecture.md` for design decisions, access matrix, and finding schema.
**Master plan reference:** See `execution-plan.md` — Phase 3, Agentic Workflows.

---

## Current Focus

**Blocked: Architecture decisions must be completed before D.2 spec is written.**

See open questions below — resolve all three groups before touching any code.

---

## ⚠️ Open Architecture Questions — Resolve Before D.2 (2026-05-04)

Architecture doc (`docs/engineering-practices/agent-architecture.md`) was updated with the Sentry Agent Query Contract. Three groups of decisions remain open.

### Group 1 — Inter-Agent Data Contracts

**Q1 — What does the Orchestrator pass to each specialist agent?**
Currently `investigate(fingerprint=abc123)` — is that the only input? Does it also pass the GitHub issue body or the error count from the monitoring workflow?

**Q2 — What does the Recommendation Agent receive?**
Full YAML findings from all agents, or only the `interpretation` sections? Passing full findings exposes raw stack traces the Recommendation Agent doesn't need. Passing only `interpretation` is leaner but may lose context the agent needs to reason well.

**Q3 — Schema validation failure behaviour**
When the Orchestrator validates a finding against the schema and it fails — does it stop routing entirely, or pass a `failed` envelope downstream?

---

### Group 2 — Per-Agent Guardrails

Sentry agents now have a query contract. The same guardrail thinking has not been applied to other agents:

| Agent | Questions to answer |
|---|---|
| Render Logs Agent | Max log lines fetched? Fields stripped before Claude context? Time window? |
| GitHub Agent | Max commits fetched? Max issue comments? Fields stripped? |
| Codebase Agent | Max files read? Max lines per file? Which paths are off-limits? |
| Recommendation Agent | Max findings payload size? Behaviour when one or more findings are `partial`? |
| Orchestrator | Max agents invoked per investigation? Timeout per agent call? |

**Q4 — Should every agent have its own query contract section in the architecture doc?**

---

### Group 3 — Token Efficiency Rules

**Q5 — Trim-at-boundary as a universal principle**
Every tool result must be trimmed to only the fields Claude needs before entering context. Currently in `agents/CLAUDE.md` only. Should this be elevated to a Principle in the architecture doc?

**Q6 — Prompt caching strategy**
`build_system_prompt()` wraps system prompts with `cache_control`. Architecture doc does not mention this. Should the caching strategy be documented — which prompts are cached, TTL implications?

**Q7 — Recommendation Agent payload**
If a Sentry finding has raw stack frames in `findings` that the Recommendation Agent doesn't need to reason about root cause — should those be stripped before handoff, and who is responsible for stripping them (Orchestrator or the Sentry agent itself)?

---

**Next task: D.2 — Backend Sentry Agent**

Build `agents/backend_sentry_agent.py` — same structure as D.1 but targets the `restaurant-backend` Sentry project. Follow the observability wiring checklist in `agents/CLAUDE.md`.

Sequence:
1. **Resolve open design question below before writing spec**
2. Write spec `agents/specs/d2_backend_sentry_agent.md` — wait for sign-off
3. Write failing test in `agents/tests/test_backend_sentry_agent.py` (red phase)
4. Implement `agents/backend_sentry_agent.py` — green phase
5. Wire `record_agent_run()` per `agents/CLAUDE.md` checklist
6. Smoke test against real backend Sentry project
7. Commit + PR → then proceed to D.3

**Path:** ~~B.2~~ ~~B.4~~ ~~B.5~~ ~~A.4~~ ~~D.1~~ ~~A.5~~ ~~DT-12~~ ~~D.1 smoke test~~ ~~DT-13~~ → D.2 → D.3 → D.4 → D.5 → D.6 → E (orchestration)

**Deferred:** 8 pre-existing ESLint warnings (`react-refresh/only-export-components`) in shadcn/ui components — separate task, not blocking agents

---

## ⚠️ Open Design Question — Agent Time Window Strategy (resolve before D.2 spec)

**Context:** During DT-13 we discovered the frontend Sentry agent was fetching 25 issues with no time boundary, pulling month-old stale errors and wasting ~21k tokens per run. We fixed it to `age:-1h` with limit 3, cutting cost from 26k to 5k tokens.

**The question:** Who controls the time window — the agent or the orchestrator?

**Constraints agreed:**
- Each agent must be **lean and confined to a fixed scope** — no superpowers across the landscape
- Each agent has one job and one data source (e.g. `restaurant-frontend` Sentry project only)
- `project_slug` must be hardcoded inside the agent — orchestrator cannot redirect an agent to a different project
- Raw API responses must never enter LLM context — trim at the boundary always

**The tension:**
- A fixed `age:-1h` window is right for live incident response but wrong for a nightly health sweep (needs 24h)
- The orchestrator knows *why* it's running — live incident vs scheduled sweep — but should not have open access to agent internals

**Proposed solution (needs sign-off):**
Agent defines a fixed menu of allowed windows. Orchestrator picks from the menu — it cannot pass arbitrary values:

```python
ALLOWED_WINDOWS = {
    "live": "age:-1h",    # default — incident response, on-call
    "daily": "age:-24h",  # morning health sweep
}

def run(window: str = "live") -> str:
    query_filter = ALLOWED_WINDOWS.get(window, ALLOWED_WINDOWS["live"])
```

- Agent stays in control of its scope — orchestrator gets a safe, bounded knob
- Unknown window values fall back to `"live"` silently — no injection possible
- All agents adopt the same `run(window="live")` signature from D.2 onwards
- D.1 `frontend_sentry_agent.py` to be retrofitted with the same signature after D.2 confirms the pattern

**Needs decision:** Is `ALLOWED_WINDOWS` the right pattern, or should time window be fully fixed per agent with no orchestrator input at all?

---

## Session Progress (2026-05-03)

**DT-13 complete. Next: D.2 Backend Sentry Agent.**

### DT-13 — Agent Observability via Sentry ✅ complete (2026-05-03)
- `agents/sentry_utils.py` — `record_agent_run()` wraps each `run()` in a Sentry transaction; `_strip_code_fence()` defensive helper added for YAML parsing; `set_data()` used (not deprecated `set_measurement()`)
- `agents/config.py` — `AGENTS_SENTRY_DSN` added (empty default = opt-in locally)
- `agents/requirements.txt` — `sentry-sdk==2.58.0` + `certifi` + `urllib3` pinned
- `agents/frontend_sentry_agent.py` — `usage_by_turn` accumulated each turn; `record_agent_run()` called before every return path; tool results trimmed: `query_sentry_errors` uses `age:-1h` + limit 3 + 6-field trim; `get_stack_trace` trimmed to exception essentials + top 2 frames only
- Token cost: 26k → 5k per run (80% reduction) after trimming
- `agents/tests/test_sentry_utils.py` — 4 TDD tests green; `COMPLETED_HIGH_YAML` uses code-fenced input to cover `_strip_code_fence`
- `agents/tests/test_frontend_sentry_agent.py` — `record_agent_run` mocked to prevent real Sentry calls
- `agents/CLAUDE.md` — observability guardrail + token efficiency rules + wiring checklist
- `.gitignore` — `agents/__pycache__/` patterns added
- `agents/specs/dt13_agent_observability.md` — post-implementation findings documented
- PR: `feat/dt13-agent-observability` — 5/5 tests passing
- **Pending:** switch `record_agent_run` to `capture_event` (Performance not on free plan); build Sentry dashboard after first production run

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

**D.1 complete.** `agents/frontend_sentry_agent.py` fully implemented and test green. Next: A.5 runbook.

### D.1 — Frontend Sentry Agent ✅
`agents/frontend_sentry_agent.py` — complete:
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
- Per-agent overrides for all 6 agents; all fall back to global defaults except: `CODEBASE_MAX_TURNS` defaults to `8` (deeper tracing), `RECOMMENDATION_MAX_TURNS` defaults to `1` (no tools, one turn only)

### `agents/requirements.txt` updated
Added `pytest==9.0.3` and its 5 transitive dependencies (colorama, iniconfig, packaging, pluggy, pygments) — all pinned.

### D.1 TDD test written — red phase confirmed
- `agents/tests/__init__.py` — empty; required so pytest resolves `from agents.frontend_sentry_agent import run` correctly when run from repo root
- `agents/tests/test_frontend_sentry_agent.py` — acceptance test for Scenario 5 (schema drift: `preparation_time` field in frontend query but missing from gateway schema)
  - `SENTRY_EVENT` — mock Sentry issue dict with TypeError on `useMenu.ts`
  - `EXPECTED_FINDING` — expected agent output: `agent=frontend-sentry`, `confidence=high`, `affected_layer=gateway`, `regression=True`, `affected_field=preparation_time`
  - `test_frontend_sentry_identifies_schema_drift()` — patches `query_sentry_errors`, calls `run()`, asserts 10 specific fields
  - **Red phase confirmed:** `AttributeError: module 'agents' has no attribute 'frontend_sentry_agent'` — module does not exist yet

### D.1 agent file started — 3 of 4 parts written
`agents/frontend_sentry_agent.py` — in progress:
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
- `agents/config.py` — 7 model constants (`ORCHESTRATOR_MODEL`, `RECOMMENDATION_MODEL`, `CODEBASE_MODEL`, `FRONTEND_SENTRY_MODEL`, `BACKEND_SENTRY_MODEL`, `RENDER_LOGS_MODEL`, `GITHUB_MODEL`) read from env vars; defaults: Sonnet 4.6 for Orchestrator/Recommendation/Codebase, Haiku 4.5 for Sentry/Render/GitHub
- `agents/prompt_utils.py` — single function `build_system_prompt(text: str) -> list[dict]`; wraps system prompt text in Anthropic SDK cache_control block; all agents must use this when building their system prompt

`agents/requirements.txt` updated with: `pydantic==2.13.3`, `pyyaml==6.0.3` (jsonschema was already present from B.1).

`.venv` is inside `agents/` — activate with `source .venv/Scripts/activate` (bash on Windows) before running any Python commands.

---

## Guiding Principles

- Build one phase at a time; validate it fully before moving to the next.
- Test scenarios (`docs/agent-test-scenarios.md`) are the acceptance criteria — an agent is not done until it passes its relevant scenarios.
- Runbook must be updated before each agent is built — agents read the runbook, not the other way around.
- No agent writes to external systems until the orchestration layer is complete and authorization logic is in place.
- Agents are Python modules in the `agents/` package using the Anthropic SDK. No Claude Code sub-agents.

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
| A.6 | Render logs access | Confirm Render API key is available as env variable; document which log endpoints the Render Logs Agent will call | ⏳ Pending |
| A.7 | Sequence diagram | Add sequence diagram to agent architecture doc showing agent transitive dependencies and Sentry release → error correlation flow | ✅ Done — release ID end-to-end flow diagram and both orchestration flow diagrams added to `agent-architecture.md` under Monitoring Workflows and Orchestration Flow sections |

---

## Phase B — Agent Package Foundation

> Establish the `agents/` Python package and shared infrastructure before any individual agent is built. Every subsequent phase depends on this.

| # | Task | Description | Status |
|---|---|---|---|
| B.1 | `agents/` package setup | Create `agents/` directory at repo root; add `requirements.txt` with `anthropic`, `jsonschema`, `PyGithub`, `requests` pinned to exact versions; `.venv` added to `.gitignore` | ✅ Done — `agents/__init__.py`, `agents/requirements.txt` (pinned versions), `agents/.venv` gitignored; merged via PR #52 `feat/agents-package` |
| B.2 | Finding schema — Pydantic models | Create `agents/schemas/models.py` — `BaseFinding` Pydantic model defines three sections: `metadata` (common envelope), `findings` (agent-observed data), `interpretation` (agent conclusion for Recommendation Agent). Agent-specific subclasses (e.g. `FrontendSentryFinding`) extend `BaseFinding` with their own `findings` fields. Generate `agents/schemas/finding-schema.json` from models via `pydantic.model_json_schema()` — never hand-edit the JSON file. **Pydantic is the single source of truth; JSON Schema file is auto-generated.** See architecture doc Finding Schema section for field definitions and rationale. Sentry agent subclasses must declare one of three release ID states in metadata: `release_id: "sha"` (present), `release_id: null` (fallback to timestamp, Recommendation Agent downgrades confidence to medium), `release_id_unresolvable: true` (SHA in Sentry but not in git history) | ✅ Done — `agents/schemas/models.py` with `BaseFinding`, `FrontendSentryFinding`; `agents/schemas/finding-schema.json` auto-generated; `pydantic==2.13.3` added to `requirements.txt`; merged via `feat/finding-schema-models` |
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

> Build and validate each agent in isolation against its relevant test scenarios. No orchestrator yet — each agent is called directly in tests.

| # | Task | Description | Status |
|---|---|---|---|
| D.1 | Frontend Sentry Agent | `agents/frontend_sentry_agent.py` — Anthropic SDK agentic loop; tools: `query_sentry_errors`, `get_stack_trace`, `get_affected_releases` (frontend project only); returns YAML finding conforming to `finding-schema.json`; validate against Scenario 5 (schema drift) | ✅ Done — all 4 parts written (`TOOLS`, system prompt, `run()` loop, partial fallback); TDD test green; merged via PR #64 `feat/d1-frontend-sentry-agent` |
| D.2 | Backend Sentry Agent | `agents/backend_sentry_agent.py` — same structure as D.1 but scoped to backend Sentry project; adds `endpoint` and `status_code` to agent-specific fields; validate against Scenario 1 (reservation failures) and Scenario 3 (allergens) | ⏳ Pending |
| D.3 | Render Logs Agent | `agents/render_logs_agent.py` — tools: `get_service_logs`, `get_deployment_events`; returns structured log entries and startup/crash events; validate against Scenario 2 (cold start) | ⏳ Pending |
| D.4 | GitHub Agent | `agents/github_agent.py` — tools: `get_issue`, `get_recent_commits`, `get_pr_history` (read-only); validate against Scenario 3 (allergens issue) and Scenario 4 (wrong total) | ⏳ Pending |
| D.5 | Codebase Agent | `agents/codebase_agent.py` — tools: `read_file`, `grep_symbol`, `git_diff` (filesystem read-only, scoped to `src/`, `graphql-gateway/`, `backend/`, `docs/`); traces field/symbol through full stack; reads runbook; validate against all 5 scenarios | ⏳ Pending |
| D.6 | Recommendation Agent | `agents/recommendation_agent.py` — no external tool access; receives structured findings from orchestrator as input; produces root cause statement, confidence level (high/medium/low), recommended fix, runbook reference, and escalation flag; validate against all 5 scenarios | ⏳ Pending |

---

## Phase E — Orchestration Layer

> Wire agents together under `orchestrator.py`. Add trigger handling, schema validation, routing logic, and authorization gating.

| # | Task | Description | Status |
|---|---|---|---|
| E.1 | Orchestrator design | Document routing logic for each of the three trigger types (monitoring workflow label event, manual GitHub issue, `/troubleshoot` skill) — which agents are invoked, in what order, under what conditions; confirm no direct Sentry webhook triggers (not used — paid feature) | ⏳ Pending |
| E.2 | Orchestrator implementation | `agents/orchestrator.py --issue <number>` — reads issue body and labels; routes to the correct Sentry agent based on `source:*` label; invokes Render Logs, Codebase, GitHub agents; validates each finding via `agents/validator.py` before routing (malformed finding → flag on issue, stop); passes validated findings to Recommendation Agent | ⏳ Pending |
| E.3 | `/troubleshoot` skill | Claude Code skill in `.claude/skills/`; accepts symptom description or GitHub issue number; shell wrapper that calls `python agents/orchestrator.py --issue <number>`; same entry point as automated path | ⏳ Pending |
| E.4 | GitHub write authorization | Implement tool-list gating in orchestrator: `post_github_comment` and `send_email` are always in the tool list; `open_pull_request` and other write tools are added to the tool list only after human comments `/approve` on the issue — before that the function does not exist in the agent's tool list; compliance flag (`pii_flag: true` in any finding) blocks `/approve` path until human comments `/compliance-acknowledged` | ⏳ Pending |
| E.5 | Confidence-gated notifications | Orchestrator reads `confidence` from Recommendation Agent finding; high → post GitHub comment + send Resend email; medium → post GitHub comment only; low → post GitHub comment only with "investigation inconclusive" framing | ⏳ Pending |
| E.6 | Timeout and escalation | Orchestrator checks for human response after 24 hours on high-confidence findings → send reminder email; after 48 hours → add `escalation-needed` label; never act autonomously on timeout — only re-notify | ⏳ Pending |

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
A.5 (runbook) ─────────────────────────────────────→ D.5 (Codebase Agent reads runbook)
A.6 (Render API) ──────────────────────────────────→ D.3 (Render Logs Agent)

B.1 (agents/ package) ─────────────────────────────→ B.2, B.3, B.4, B.5, all of D and E
B.2 (finding schema) ──────────────────────────────→ B.3 (validator), D.1–D.6 (agents conform to schema)
B.3 (schema validator) ────────────────────────────→ E.2 (orchestrator validates before routing)
B.4 (model config) ────────────────────────────────→ D.1–D.6, E.2
B.5 (prompt caching) ──────────────────────────────→ D.1–D.6, E.2 (all agents must cache system prompts)

C.1 (backend monitor workflow) ────────────────────→ C.3 (orchestrator triggered by label)
C.2 (frontend monitor workflow) ───────────────────→ C.3 (orchestrator triggered by label)
C.3 (agent-orchestrator.yml) ──────────────────────→ E.2 (entry point for automated path)

D.1–D.6 (all agents) ──────────────────────────────→ E.2 (Orchestrator invokes them)
E.2 (Orchestrator) ────────────────────────────────→ E.3, E.4, E.5, E.6
E.2–E.6 (full orchestration) ──────────────────────→ F.1–F.7
```
