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
6. **Human in the loop — always.** Agents recommend; humans decide. No agent takes a write action (posting a comment, opening a PR, modifying configuration) without explicit human approval. The notification mechanism is the bridge between agent output and human decision.

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
**Responsibility:** Receive triggers, route to the right agents, collect findings, pass to Recommendation Agent, notify the human, and execute approved actions.
**Access:** Can invoke all agents; can open GitHub Issues and send email (Resend) for notifications; executes write actions only after human approval
**Inputs:** trigger event (see Trigger Types below); human approval/rejection responses
**Outputs:** GitHub Issue with investigation findings; email notification for high-confidence findings; approved actions executed post human sign-off

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
  → Recommendation Agent (synthesize → confidence level + root cause + recommended fix)
  → Orchestrator opens GitHub Issue with full findings
  → [high confidence] Orchestrator sends email notification via Resend
  → Human reviews → /approve / /reject / /investigate
  → [approved] Orchestrator executes recommended action
```

### Reactive (GitHub issue / manual)
```
Trigger (issue number or symptom)
  → Orchestrator
  → GitHub Agent (read the issue and recent related PRs)
  → Sentry Agent (find matching errors in the time window of the issue)
  → Render Logs Agent (check operational health at the time of the issue)
  → Codebase Agent (trace the symptom through the stack)
  → Recommendation Agent (synthesize → confidence level + root cause + recommended fix)
  → Orchestrator comments on the GitHub Issue with findings
  → [high confidence] Orchestrator sends email notification via Resend
  → Human reviews → /approve / /reject / /investigate
  → [approved] Orchestrator executes recommended action
```

---

## Human in the Loop

No agent recommendation is acted upon without human review. The orchestrator packages the Recommendation Agent's output and notifies the human before taking any write action. The human then approves, rejects, or requests further investigation.

### Notification Channels

| Channel | When used |
|---|---|
| GitHub Issue | Primary channel — opened automatically for every investigation that produces a finding; contains full root cause, evidence summary, and recommended action |
| Email (Resend) | Secondary channel — sent alongside the GitHub Issue for high-confidence findings that require prompt attention |

The GitHub Issue is the record of the investigation. The email is the nudge that a human needs to look at it. Both point to the same issue.

### Confidence-Gated Actions

The Recommendation Agent assigns a confidence level to every output. The orchestrator uses this to determine what the agent does next and what the notification says.

| Confidence | Agent action | Notification content |
|---|---|---|
| **High** — root cause clear, fix is bounded | Open GitHub Issue with full diagnosis + specific recommended fix; notify human via email | "Root cause identified. Recommended fix attached. Please approve to proceed." |
| **Medium** — likely cause known, needs human judgement | Open GitHub Issue with diagnosis and 2–3 proposed approaches; no email | "Likely cause identified. Human judgement needed to choose approach." |
| **Low** — complex or cross-cutting, root cause unclear | Open GitHub Issue with raw findings and what was ruled out; no email | "Investigation inconclusive. Human investigation required." |

### Human Response Options

When the human reviews the GitHub Issue, they have three options:

- **Approve** — comment `/approve` on the issue; orchestrator proceeds with the recommended action (e.g. posts a fix PR, updates configuration)
- **Reject** — comment `/reject [reason]`; orchestrator closes the investigation and logs the rejection reason
- **Request more investigation** — comment `/investigate [additional context]`; orchestrator re-runs with the additional context as input

### Timeout and Escalation

- If no human response within **24 hours** on a high-confidence finding, a reminder email is sent
- If no response within **48 hours**, the issue is escalated with an `escalation-needed` label
- The orchestrator never acts on a timeout — it only re-notifies; human approval is required regardless of elapsed time

### What the Agent Can Never Do Without Approval

- Post a comment on a GitHub Issue on behalf of the system
- Open or close a pull request
- Modify any configuration file or environment variable
- Trigger a redeployment
- Send a notification to a customer-facing channel

---

## Runbook Integration

Every investigation the Recommendation Agent performs must reference `docs/runbooks/troubleshooting.md`. The runbook maps known error patterns to investigation steps and expected findings. If the agent cannot find a matching pattern in the runbook, it flags the investigation as low confidence and recommends a human review.

The runbook is the shared knowledge base between human on-call engineers and agents — it must be kept current as new scenarios are discovered.

---

## Test Scenarios

Agent behaviour is validated against five documented scenarios in `docs/agent-test-scenarios.md`. Each scenario defines the trigger, the expected agent routing, the expected findings per agent, and the expected recommendation. A new agent implementation is not considered complete until it passes all five scenarios.
