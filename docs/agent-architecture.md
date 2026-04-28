# Agent Architecture — Aap ki Rasoi

**Status: DRAFT**
**Last updated: 2026-04-28**
**Workflow context:** See `docs/engineering-practices/ai-agent-workflow.md` — two-loop model (inner/outer), signal sources, and recommended agent behaviour.
**Implementation plan:** See `docs/agent-execution-plan.md` — phases, tasks, and validation scenarios.

---

## Principles

1. **Specialized agents over monolithic agents.** Each agent does one job and does it well. No agent reads from all sources or makes all decisions.
2. **Least privilege.** Each agent has access only to the external systems it needs. An agent that reads Sentry has no access to GitHub. An agent that reads code has no access to external APIs.
3. **Orchestration layer.** A single orchestrator receives triggers, decides which agents to invoke, and synthesizes findings. Agents do not call each other — all coordination goes through the orchestrator.
4. **Structured handoffs.** Agents return structured findings (not free-form prose) so the orchestrator and recommendation layer can reliably parse and combine them.
5. **Read before write.** No agent writes to any external system (GitHub, Sentry, Slack) unless explicitly authorized by the orchestrator. Write access is a deliberate escalation, not a default.

---

## Agent Catalog

### Sentry Agent
**Responsibility:** Query Sentry for errors, trends, and patterns.
**Access:** Sentry API — read-only
**Inputs:** time range, feature filter, error type filter
**Outputs:** error list with stack traces, trend data (frequency over time), affected release tags

### Render Logs Agent
**Responsibility:** Read runtime and deployment logs from Render.
**Access:** Render API — read-only
**Inputs:** service name, time range, log level filter
**Outputs:** structured log entries, server startup events, request/response entries, crash events

### GitHub Agent
**Responsibility:** Read GitHub issues and recent commits/PRs.
**Access:** GitHub API — read-only (write access granted only for posting investigation comments, explicitly requested by orchestrator)
**Inputs:** issue number or label filter, commit range
**Outputs:** issue description and comments, recent commits with messages and changed files, PR merge times

### Codebase Agent
**Responsibility:** Read and trace relevant source files, runbooks, and schemas.
**Access:** Filesystem — read-only, scoped to paths relevant to the investigation (`src/`, `graphql-gateway/`, `backend/`, `docs/`)
**Inputs:** file paths, symbol names, field names to trace
**Outputs:** code snippets, field trace (component → hook → query → resolver → backend), runbook steps for the identified pattern

### Recommendation Agent
**Responsibility:** Synthesize findings from all other agents into a root cause statement and actionable recommendation.
**Access:** None — receives only structured findings passed in from the orchestrator
**Inputs:** structured findings from Sentry Agent, Render Logs Agent, GitHub Agent, Codebase Agent
**Outputs:** root cause statement, confidence level (high/medium/low), recommended fix, suggested runbook section, escalation flag if confidence is low

### Orchestrator
**Responsibility:** Receive triggers, route to the right agents, collect findings, pass to Recommendation Agent, deliver final output.
**Access:** Can invoke all agents; can authorize GitHub Agent to post a comment if confidence is high
**Inputs:** trigger event (see Trigger Types below)
**Outputs:** investigation report delivered to the appropriate channel (GitHub issue comment, console, or alert)

---

## Access Matrix

| Agent | Sentry | Render Logs | GitHub (read) | GitHub (write) | Codebase | External write |
|---|---|---|---|---|---|---|
| Sentry Agent | ✅ Read | ❌ | ❌ | ❌ | ❌ | ❌ |
| Render Logs Agent | ❌ | ✅ Read | ❌ | ❌ | ❌ | ❌ |
| GitHub Agent | ❌ | ❌ | ✅ Read | Orchestrator only | ❌ | ❌ |
| Codebase Agent | ❌ | ❌ | ❌ | ❌ | ✅ Read | ❌ |
| Recommendation Agent | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Orchestrator | Via agents | Via agents | Via agents | ✅ Authorized | Via agents | ❌ |

---

## Trigger Types

| Trigger | Source | Orchestrator Entry Point |
|---|---|---|
| Scheduled proactive check | Cron (daily) | Check Sentry for error spikes; check Render for operational anomalies |
| GitHub issue opened | GitHub webhook or manual invocation | Read issue → extract symptom → investigate |
| Sentry alert threshold crossed | Sentry alert webhook | Read error group → investigate |
| Manual invocation | `/troubleshoot` skill | User provides symptom or issue number → investigate |

---

## Orchestration Flow

### Proactive (scheduled / Sentry alert)
```
Trigger
  → Orchestrator
  → Sentry Agent (look for error spikes or new patterns)
  → [if issues found] Render Logs Agent (confirm operational health)
  → [if issues found] Codebase Agent (trace the affected field/path)
  → [if issues found] GitHub Agent (check for recent commits touching the affected area)
  → Recommendation Agent (synthesize)
  → Output: alert report with root cause and recommendation
```

### Reactive (GitHub issue / manual)
```
Trigger (issue number or symptom)
  → Orchestrator
  → GitHub Agent (read the issue and recent related PRs)
  → Sentry Agent (find matching errors in the time window of the issue)
  → Render Logs Agent (check operational health at the time of the issue)
  → Codebase Agent (trace the symptom through the stack)
  → Recommendation Agent (synthesize)
  → Output: investigation report posted as GitHub issue comment (if authorized)
```

---

## Runbook Integration

Every investigation the Recommendation Agent performs must reference `docs/runbooks/troubleshooting.md`. The runbook maps known error patterns to investigation steps and expected findings. If the agent cannot find a matching pattern in the runbook, it flags the investigation as low confidence and recommends a human review.

The runbook is the shared knowledge base between human on-call engineers and agents — it must be kept current as new scenarios are discovered.

---

## Test Scenarios

Agent behaviour is validated against five documented scenarios in `docs/agent-test-scenarios.md`. Each scenario defines the trigger, the expected agent routing, the expected findings per agent, and the expected recommendation. A new agent implementation is not considered complete until it passes all five scenarios.
