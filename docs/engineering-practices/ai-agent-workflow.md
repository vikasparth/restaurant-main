# AI Agent Workflow — Development to Production

**Scope:** All engineers and AI agents working in this repository.
**Last updated:** 2026-04-28
**Agent architecture:** See `docs/engineering-practices/agent-architecture.md` — specialized agents, access matrix, orchestration layer, and least privilege design.
**Agent implementation plan:** See `docs/engineering-practices/agent-execution-plan.md` — phases, tasks, and validation scenarios.

> **Note on CI tooling:** The inner loop diagram shows frontend tools (Husky, ESLint, TypeScript, Vitest). Backend uses pre-commit framework, Black, Flake8, and pytest. The phases and principles are identical — only the tool names differ. When the repo splits, each team copies this file and updates the tool names for their stack.

---

## Two Loops, Not One

The agent participates in two distinct cycles:

- **Inner loop — Execution:** A task is assigned. The agent writes code, opens a PR, CI runs, human reviews, merges. Linear flow from development to production.
- **Outer loop — Operations:** The agent monitors production signals, researches context, and proposes work without being explicitly assigned. A continuous cycle that feeds back into the inner loop.

---

## Inner Loop — Development to Production

```mermaid
sequenceDiagram
    actor Dev as Developer / GenAI Agent
    participant Local as Local Machine
    participant Branch as Feature Branch
    participant GH as GitHub
    participant CI as GitHub Actions
    participant Human as Human Reviewer
    participant Main as main (protected)
    participant Deploy as Deploy Service
    participant Prod as Production
    participant Monitor as Sentry + Canary

    rect rgb(220, 235, 255)
        note over Dev, Branch: Phase 1 — Local Development
        Dev->>Local: git commit
        Local->>Local: Pre-commit hook fires
        Local->>Local: Lint and format check on staged files only
        alt Fails
            Local-->>Dev: Commit rejected — fix before committing
        else Passes
            Local-->>Dev: Commit accepted
        end
        Dev->>Branch: git push  feature/task-name
    end

    rect rgb(255, 243, 220)
        note over Branch, GH: Phase 2 — Pull Request
        Dev->>GH: Opens PR  feature/task-name to main
        note over GH: Branch protection rules<br/>CI must pass before merge<br/>1 human approval required<br/>No direct push to main<br/>Stale approval dismissed on new push
        GH->>CI: Triggers ci.yml on pull_request event
    end

    rect rgb(220, 255, 220)
        note over CI: Phase 3 — CI Checks
        CI->>CI: TypeScript compile — zero type errors
        CI->>CI: ESLint — zero warnings
        CI->>CI: Frontend build
        CI->>CI: Schema validator — every GraphQL field vs openapi.json
        CI->>CI: graphql-inspector — breaking schema changes vs main
        alt Any check fails
            CI-->>GH: Status FAILED
            GH-->>Human: Red cross on PR — merge button locked
            Human->>Dev: Investigate failure in Actions tab
            Dev->>Branch: Push fix — CI re-triggers
        else All checks pass
            CI-->>GH: Status PASSED
            GH-->>Human: Green tick — merge unlocked
        end
    end

    rect rgb(255, 245, 220)
        note over Human, Main: Phase 4 — Human Review
        Human->>Human: Reviews intent, logic, design
        alt Changes requested
            Human-->>Dev: Review comment on PR
            Dev->>Branch: Push fix — CI re-triggers
        else Approved and CI green
            Human->>GH: Approves PR
            GH->>Main: Merges to main
            GH->>Branch: Feature branch deleted
        end
    end

    rect rgb(235, 220, 255)
        note over Main, Prod: Phase 5 — Deploy
        Main->>Deploy: Merge to main triggers deploy pipeline
        Deploy->>Prod: Build and deploy to production
        Deploy-->>GH: Deploy status posted back to PR
    end

    rect rgb(220, 245, 255)
        note over Prod, Monitor: Phase 6 — Observation Layer (always on — see diagram below)
        Prod-->>Monitor: Frontend JS errors → Sentry via logger.ts
        Prod-->>Monitor: Gateway errors → Sentry via @sentry/node
        Prod-->>Monitor: Backend errors → Render logs via Python structured logging
        Monitor->>Prod: Canary tests every 50 min (GitHub Actions)
        Monitor->>Prod: UptimeRobot HTTP check every 5 min
        alt Alert condition
            Monitor->>GH: Auto-opens canary-failure issue
            GH-->>Human: Email notification
        else Recovered
            Monitor->>GH: Auto-closes canary-failure issue
        end
        Monitor-->>Dev: Sentry dashboard — error notifications
    end
```

---

## Observation Layer

Three independent logging stacks run continuously in production — one per tier. They are always on, independent of deployment events, and feed directly into the outer loop signal sources.

```mermaid
flowchart TD
    subgraph Prod["Production — Three Tiers"]
        FE["Frontend\nVercel CDN\n@sentry/react"]
        GW["GraphQL Gateway\nVercel Node.js\n@sentry/node"]
        BE["Backend\nRender FastAPI\nPython structured logging"]
    end

    subgraph Obs["Observation Layer (always on)"]
        SE["Sentry\nFrontend and Gateway errors\nStack traces · ARIA breadcrumbs\nbeforeBreadcrumb hook normalises selectors"]
        RL["Render Logs\nJSON per request in production\nrequest_id · event · reference\nNever logs PII"]
        CA["Canary Tests\nGitHub Actions every 50 min\nUptimeRobot every 5 min\nHealth · menu · delivery endpoints"]
        AI["AI Monitor Agent\ncron-job.org → /api/internal/monitor\nRule-based threshold checks\nTwo consecutive 6h windows"]
    end

    FE -- "logger.ts → Sentry.captureException()\nOnly unknown errors — expected\nbusiness errors handled in UI" --> SE
    GW -- "Sentry.init() before Apollo Server\nCaptures unhandled resolver errors" --> SE
    BE -- "logger.exception() in routers\nlogger.info() in services\nOn every business event" --> RL

    RL --> AI
    CA -->|"health · menu · delivery"| FE & GW & BE

    SE -->|"new or spiked error"| Alert["Developer notified\nSentry dashboard"]
    CA -->|"endpoint failure"| Issue["GitHub Issue auto-opened\ncanary-failure label + owner email"]
    AI -->|"threshold breached"| Issue
    AI -->|"metrics recover"| Close["GitHub Issue auto-closed"]
```

### What each stack captures

| Stack | Tool | Captures | Does not capture |
|---|---|---|---|
| Frontend | `@sentry/react` + `logger.ts` | Unhandled JS exceptions, explicit `logger.error()` calls | Expected business errors (ZIP not covered, sold out) — those are handled in UI |
| Gateway | `@sentry/node` | Unhandled resolver errors, uncaught gateway exceptions | GraphQL user errors (those are returned in the `errors` field, not thrown) |
| Backend | Python `logging` + Render | Every router failure (`logger.exception`), every business event created (`logger.info`) | Frontend and gateway events — each tier owns its own stack |
| Canary | GitHub Actions + UptimeRobot | Endpoint availability and correctness on a schedule | Silent data corruption, logic errors that still return 200 |
| AI Monitor | cron-job.org agent | Error rate trends, latency spikes, notification failure patterns | Anything requiring human design judgement |

---

## Outer Loop — Agent Operations Cycle

The agent does not only execute assigned tasks. It monitors three signal sources continuously and one on a schedule, researches context from multiple sources, and proposes work proactively. Every proposal feeds back into the inner loop.

```mermaid
flowchart TD
    subgraph Signals["Signal Sources"]
        S1["🔴 Sentry alert\nError spike or new unhandled exception\nin frontend, gateway, or backend"]
        S2["🟡 Canary failure\nEndpoint returning errors or timing out\ndetected every 50 min"]
        S3["🔵 New GitHub Issue\nOpened by human, by canary auto-open,\nor escalated by a previous agent run"]
        S4["🟢 Scheduled review\nPeriodic proactive scan — error patterns,\ntech debt, doc drift"]
    end

    S1 & S2 & S3 & S4 --> ORCH["Orchestrator\nDecides which agents to invoke\nbased on trigger type and symptom"]

    subgraph Agents["Specialized Agents — Least Privilege"]
        ORCH --> A1["Frontend Sentry Agent\nJS errors · React breadcrumbs\nFrontend Sentry project only"]
        ORCH --> A2["Backend Sentry Agent\nPython exceptions · FastAPI errors\nBackend Sentry project only"]
        ORCH --> A3["Render Logs Agent\nRuntime and startup logs\nRender API only"]
        ORCH --> A4["GitHub Agent\nIssues · commits · PRs\nGitHub read-only"]
        ORCH --> A5["Diagnostic Agent\nSource files · runbook · schemas\nFilesystem read-only — scoped paths"]
    end

    A1 & A2 & A3 & A4 & A5 --> REC["Coding Agent\nSynthesizes structured findings\nNo external access"]

    REC --> CONF{Confidence level}

    CONF -->|"High — root cause clear,\nfix is bounded"| N1["Orchestrator opens GitHub Issue\n+ sends email via Resend"]
    CONF -->|"Medium — likely cause known,\nneeds human judgement"| N2["Orchestrator opens GitHub Issue\nno email"]
    CONF -->|"Low — complex or cross-cutting,\nroot cause unclear"| N3["Orchestrator opens GitHub Issue\nflags for human investigation"]

    N1 & N2 & N3 --> HUMAN["👤 Human reviews GitHub Issue\n/approve · /reject · /investigate"]

    HUMAN -->|"/approve"| ACT["Orchestrator executes\napproved action"]
    HUMAN -->|"/reject"| CLOSE["Investigation closed\nReason logged on issue"]
    HUMAN -->|"/investigate [context]"| ORCH

    ACT --> INNER["Back to inner loop\nCI checks → Human Review → Merge"]
```

---

## Signal Sources Explained

| Signal | What triggers it | What the agent reads |
|---|---|---|
| **Sentry error spike** | Error rate exceeds threshold or new unhandled exception | Stack trace, source file at the line, recent commits that may have introduced it |
| **Sentry new error type** | Error class never seen before in production | Where in the codebase this originates, whether tests cover the scenario |
| **Canary failure** | Health, menu, or delivery endpoint fails or times out | Backend logs, recent deployments, historical canary failures for the same endpoint |
| **New GitHub Issue** | Human reports a bug, canary auto-opens, or agent escalates | Issue description, historical issues for similar reports, relevant source files |
| **Scheduled review** | Periodic run | Stale TODOs, test gaps, documentation drift vs current code, recurring error patterns |

---

## What Each Layer Catches

| Layer | Catches | Does not catch |
|---|---|---|
| Pre-commit | Lint and format errors on staged files | Type errors, build failures, whole-project issues |
| CI — build | Compile errors, broken imports, missing modules | Runtime logic errors |
| CI — lint | Lint violations across the whole project | Issues outside lint rule coverage |
| CI — tests | Unit test regressions | Integration failures, end-to-end behaviour |
| CI — schema validator | GraphQL fields missing from backend openapi.json | Runtime data shape mismatches |
| CI — graphql-inspector | Breaking GraphQL schema changes vs main | Non-breaking drift |
| Human review | Intent, logic, and design problems | Anything automated checks already cover |
| Canary + Sentry | Production runtime failures | Pre-production issues |
| **Agent ops loop** | **Error trends, recurring bugs, doc drift — patterns CI cannot see** | **Issues requiring human design judgement** |

---

## Recommended Behaviour for a GenAI Agent

**When executing an assigned task (inner loop):**
1. Pull `main` before branching — never branch from stale code
2. Create a feature branch per task — never commit directly to `main`
3. Batch all changes for a task into one PR — one task, one PR, one review cycle
4. Open as Draft PR if work is incremental — get CI feedback before requesting review
5. Wait for CI to pass before requesting human review
6. Fix the root cause of CI failures — do not push workarounds

**When operating autonomously (outer loop):**
1. Always read historical issues before proposing a fix — the pattern may be known
2. Always read the relevant source files — do not propose changes based on issue title alone
3. Open a Draft PR for bounded fixes; open a GitHub Issue for anything requiring human judgement
4. Include your full diagnosis in the PR or issue — the human should not have to re-investigate
5. Never merge without human approval — the outer loop proposes, the human decides

---

## Implementation Constraint — Selective Context Loading

The outer loop is implemented as a fleet of specialized agents under an orchestration layer, not a single agent that loads everything. Each specialized agent has access only to the systems it needs (least privilege) and loads only what is relevant to its task. See `docs/agent-architecture.md` for the full agent catalog, access matrix, and orchestration flow.

The rule within each agent: **start lean, load incrementally, stop when the finding is complete.**

```
Sentry Agent: load only the error summary for the relevant time window
  → if stack trace points to a file, load only that file's relevant section
  → return structured findings to the orchestrator — stop there

Diagnostic Agent: load only the file or symbol named by the orchestrator
  → trace one level at a time — component → hook → query → resolver
  → return the trace — stop there
```

Specialization enforces least privilege by design — a Sentry Agent cannot read source files, a Diagnostic Agent cannot read Sentry. This is a security and reliability property, not just a performance one. The orchestrator synthesizes findings across agents; no single agent needs the full picture.

See [`docs/phase2/agentic-workflows.md`](../phase2/agentic-workflows.md) for agent guardrails (security, blast radius, cost caps) and the operational incident loop design.

---

## Note on Future Repo Split

When frontend and backend move to separate repositories, each team copies this file and updates the CI tool names in the inner loop diagram for their stack. The two-loop structure, signal sources, investigation phase, and agent behaviour rules apply equally to both teams.
