# AI Agent Workflow — Development to Production

**Scope:** All engineers and AI agents working in this repository.
**Last updated:** 2026-04-24

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
        CI->>CI: Build check — compile and bundle
        CI->>CI: Lint check — whole project
        CI->>CI: Test suite
        CI->>CI: Future — Schema validator
        CI->>CI: Future — graphql-inspector
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
        note over Prod, Monitor: Phase 6 — Production Monitoring
        Monitor->>Prod: Canary tests every 50 min
        alt Canary fails
            Monitor->>GH: Auto-opens issue — canary-failure label
            GH-->>Human: Email notification
        else Canary recovers
            Monitor->>GH: Auto-closes canary-failure issue
        end
        Prod-->>Monitor: Runtime errors captured by Sentry
    end
```

---

## Outer Loop — Agent Operations Cycle

The agent does not only execute assigned tasks. It monitors three signal sources continuously and one on a schedule, researches context from multiple sources, and proposes work proactively. Every proposal feeds back into the inner loop.

```mermaid
flowchart TD
    subgraph Signals["Signal Sources"]
        S1["🔴 Sentry\nError spike or new unhandled exception\nin frontend, backend, or gateway"]
        S2["🟡 Canary failure\nEndpoint returning errors or timing out\ndetected every 50 min"]
        S3["🔵 New GitHub Issue\nOpened by human, by canary auto-open,\nor escalated by a previous agent run"]
        S4["🟢 Scheduled review\nPeriodic agent run — scans for\nerror patterns, tech debt, doc drift"]
    end

    S1 & S2 & S3 & S4 --> A[Agent picks up signal]

    subgraph Research["Investigation Phase"]
        A --> B1["Read Sentry logs\nStack traces, error frequency,\naffected users"]
        A --> B2["Read source files\nFiles referenced in stack trace\nor issue description"]
        A --> B3["Search historical GitHub Issues\nSame or similar error patterns\nfrom the past"]
        A --> B4["Read documentation and ADRs\nArchitecture decisions, known constraints,\nprevious fix attempts"]
    end

    B1 & B2 & B3 & B4 --> C{Agent confidence}

    C -->|"High\nRoot cause clear,\nfix is bounded"| D["Create feature branch\nWrite fix\nOpen Draft PR with full diagnosis"]
    C -->|"Medium\nLikely cause known,\nneeds human judgement"| E["Create GitHub Issue\nWith diagnosis, stack trace,\nand proposed approaches"]
    C -->|"Low\nComplex or cross-cutting,\nneeds design decision"| F["Create GitHub Issue\nWith full analysis\nRequest human design input"]

    D --> G["Back to inner loop\nCI checks → Human Review → Merge"]
    E --> H["Human picks up issue\nAssigns or resolves"]
    F --> H
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
| CI — schema validator *(future)* | GraphQL fields missing from backend openapi.json | Runtime data shape mismatches |
| CI — graphql-inspector *(future)* | Breaking GraphQL schema changes vs main | Non-breaking drift |
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

## Note on Future Repo Split

When frontend and backend move to separate repositories, each team copies this file and updates the CI tool names in the inner loop diagram for their stack. The two-loop structure, signal sources, investigation phase, and agent behaviour rules apply equally to both teams.
