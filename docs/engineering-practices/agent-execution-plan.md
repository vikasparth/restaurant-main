# Agent Implementation Execution Plan — Aap ki Rasoi

**Status: DRAFT**
**Last updated: 2026-04-28**
**Reference:** See `docs/engineering-practices/agent-architecture.md` for design decisions and access matrix.
**Master plan reference:** See `execution-plan.md` — Phase 3, Agentic Workflows.

---

## Guiding Principles

- Build one agent at a time, validate it in isolation before wiring to the orchestrator.
- Test scenarios (`docs/agent-test-scenarios.md`) are the acceptance criteria — an agent is not done until it passes its relevant scenarios.
- Runbook must be updated before each agent is built — agents read the runbook, not the other way around.
- No agent writes to external systems until the orchestration layer is complete and authorization logic is in place.

---

## Phase A — Prerequisites

> Must be complete before any agent is built. Agents are only as good as their signal quality.

| # | Task | Description | Status |
|---|---|---|---|
| A.1 | Backend Sentry | Install `sentry-sdk[fastapi]` on backend; wire to FastAPI; tag releases with commit SHA so errors map to deployments | ✅ Done |
| A.2 | Sentry release tagging in CI | Separate `sentry-release.yml` workflow fires on push to main; tags release with Git SHA via `getsentry/action-release@v1` | ✅ Done |
| A.3 | Test scenarios file | Write `docs/agent-test-scenarios.md` — 5 real bugs introduced one at a time to production; each scenario defines trigger, expected agent routing, expected findings, expected recommendation | ⏳ Pending |
| A.4 | Runbook coverage | Create `docs/runbooks/troubleshooting.md` — cover all 5 test scenarios with named pattern, investigation steps, and expected findings | ⏳ Pending |
| A.5 | Render logs access | Confirm Render API key is available as env variable; document which log endpoints the Render Logs Agent will use | ⏳ Pending |
| A.6 | Sequence diagram | Add sequence diagram to agent architecture doc showing agent transitive dependencies and Sentry release → error correlation flow | ⏳ Pending (after all agents designed) |

---

## Phase B — Individual Agents

> Build and validate each agent in isolation against its relevant test scenarios. No orchestrator yet.

| # | Task | Description | Status |
|---|---|---|---|
| B.1 | Sentry Agent | Claude Code agent with Sentry MCP; reads error list, trends, stack traces; returns structured findings; validate against Scenario 1 (reservation failures) and Scenario 3 (allergens) | ⏳ Pending |
| B.2 | Render Logs Agent | Claude Code agent with Render API access; reads runtime and startup logs; returns structured log entries; validate against Scenario 2 (cold start) | ⏳ Pending |
| B.3 | GitHub Agent | Claude Code agent with GitHub MCP (read-only); reads issues and recent commits; validate against Scenario 3 (allergens issue) and Scenario 4 (wrong total issue) | ⏳ Pending |
| B.4 | Codebase Agent | Claude Code agent with filesystem read (scoped paths); traces field/symbol through stack; reads runbook; validate against all 5 scenarios | ⏳ Pending |
| B.5 | Recommendation Agent | Synthesizes structured findings from all agents; produces root cause, confidence level, recommendation, and runbook reference; no external access; validate against all 5 scenarios | ⏳ Pending |

---

## Phase C — Orchestration Layer

> Wire agents together under the orchestrator. Add trigger handling and routing logic.

| # | Task | Description | Status |
|---|---|---|---|
| C.1 | Orchestrator design | Document routing logic for each trigger type (proactive, GitHub issue, Sentry alert, manual) — which agents are invoked, in what order, and under what conditions | ⏳ Pending |
| C.2 | Orchestrator implementation | Implement orchestrator as a Claude Code agent that invokes specialized agents via the Agent tool; handles all four trigger types | ⏳ Pending |
| C.3 | `/troubleshoot` skill | Expose manual trigger as a Claude Code skill; accepts symptom description or GitHub issue number; invokes orchestrator | ⏳ Pending |
| C.4 | Scheduled proactive check | Wire cron trigger (daily) to orchestrator proactive flow; output goes to a designated channel or GitHub discussion | ⏳ Pending |
| C.5 | GitHub write authorization | Implement authorization logic in orchestrator: only post GitHub issue comment if Recommendation Agent confidence is high; human review required for low/medium confidence | ⏳ Pending |

---

## Phase D — Validation

> Run the complete agent stack against all five test scenarios end-to-end.

| # | Task | Description | Status |
|---|---|---|---|
| D.1 | Scenario 1 — Reservation failures (proactive) | Trigger: scheduled check; agent detects spiking validation errors; traces to date limit rule; recommends fix | ⏳ Pending |
| D.2 | Scenario 2 — Render cold start (infrastructure) | Trigger: scheduled check; agent correlates Sentry 503s with Render startup log; rules out code bug; recommends keep-alive or tier upgrade | ⏳ Pending |
| D.3 | Scenario 3 — Missing allergens (GitHub issue) | Trigger: GitHub issue opened; agent traces null field from frontend → query → schema → resolver → backend; recommends adding field back to query | ⏳ Pending |
| D.4 | Scenario 4 — Wrong order total (GitHub issue) | Trigger: GitHub issue opened; agent traces total → mutation input → menu query → seed data; identifies price entry error | ⏳ Pending |
| D.5 | Scenario 5 — Schema drift (proactive) | Trigger: Sentry alert; agent detects undefined field in order confirmation; traces to resolver/schema gap; recommends running validate-schema.js | ⏳ Pending |
| D.6 | False positive check | Run proactive check against a clean system with no active issues; confirm agent does not raise spurious alerts | ⏳ Pending |

---

## Dependencies

```
A.1 (backend Sentry) → B.1 (Sentry Agent can read backend errors)
A.2 (release tagging) → B.1 (errors map to deployments)
A.3 (test scenarios) → B.1–B.5 (acceptance criteria)
A.4 (runbook) → B.4 (Codebase Agent reads runbook)
A.5 (Render API) → B.2 (Render Logs Agent)
B.1–B.5 (all agents) → C.2 (Orchestrator)
C.2 (Orchestrator) → C.3, C.4, C.5
C.2–C.5 → D.1–D.6
```
