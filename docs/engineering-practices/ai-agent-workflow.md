# AI Agent Workflow — Development to Production

**Scope:** All engineers and AI agents working in this repository.
**Last updated:** 2026-04-24

---

## Why Guardrails Matter More for AI-Generated Code

A human engineer typically opens a few PRs per day. An AI agent can open many PRs in rapid succession. Even a small error rate (say, 5%) becomes a real problem at volume — one broken change every twenty PRs reaching production without checks is unacceptable.

Guardrails exist so that:
- **Objective failures** (type errors, broken builds, schema drift) are caught automatically, without human effort
- **Human review** focuses on what only a human can judge: intent, logic, design quality
- **The combination** — automated checks + human approval — is stronger than either alone

---

## Full Guardrail Chain — Development to Production

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
        Local->>Local: Husky pre-commit hook fires
        Local->>Local: lint-staged — ESLint + Prettier on staged .ts/.tsx only
        alt Lint or format fails
            Local-->>Dev: Commit rejected — fix before committing
        else Passes
            Local-->>Dev: Commit accepted
        end
        Dev->>Branch: git push  feature/task-name
    end

    rect rgb(255, 243, 220)
        note over Branch, GH: Phase 2 — Pull Request
        Dev->>GH: Opens PR  feature/task-name to main
        note over GH: Branch protection rules active<br/>CI must pass before merge<br/>1 human approval required<br/>No direct push to main<br/>Stale approval dismissed on new push
        GH->>CI: Triggers ci.yml on pull_request event
    end

    rect rgb(220, 255, 220)
        note over CI: Phase 3 — CI Checks (GitHub Actions)
        CI->>CI: npm run build — TypeScript compile and Vite bundle
        CI->>CI: npm run lint — ESLint across whole project
        CI->>CI: npm test — Vitest unit tests
        CI->>CI: Future 3.16.7 — Schema validator GraphQL fields vs openapi.json
        CI->>CI: Future 3.16.8 — graphql-inspector breaking schema changes vs main
        alt Any check fails
            CI-->>GH: Status FAILED
            GH-->>Human: Red cross on PR — merge button locked
            Human->>Dev: Investigate failure in Actions tab
            Dev->>Branch: Push fix — CI re-triggers, concurrency cancels old run
        else All checks pass
            CI-->>GH: Status PASSED
            GH-->>Human: Green tick — merge unlocked, ready for review
        end
    end

    rect rgb(255, 245, 220)
        note over Human, Main: Phase 4 — Human Review
        Human->>Human: Reviews intent, logic, design — things CI cannot check
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
        note over Prod, Monitor: Phase 6 — Production Monitoring (always on)
        Monitor->>Prod: Canary tests every 50 min — health, menu, delivery endpoints
        alt Canary fails
            Monitor->>GH: Auto-opens issue with label canary-failure
            GH-->>Human: Email notification
        else Canary recovers
            Monitor->>GH: Auto-closes canary-failure issue
        end
        Prod-->>Monitor: Runtime errors captured by Sentry — frontend, backend, gateway
    end
```

---

## What Each Layer Catches

| Layer | Catches | Does not catch |
|---|---|---|
| Pre-commit (Husky) | Lint errors and formatting on staged files only | Type errors, build failures, whole-project issues |
| CI — build | TypeScript compile errors, broken imports, missing modules | Runtime logic errors |
| CI — lint | ESLint violations across the whole project | Issues in files not covered by lint rules |
| CI — tests | Unit test regressions | Integration failures, end-to-end behaviour |
| CI — schema validator *(future)* | GraphQL fields not present in backend openapi.json | Runtime data shape mismatches |
| CI — graphql-inspector *(future)* | Breaking GraphQL schema changes vs main | Non-breaking drift |
| Human review | Intent problems, logic errors, design issues | Anything automated checks already covered |
| Canary + Sentry | Production runtime failures | Pre-production issues |

---

## Recommended Behaviour for a GenAI Agent

1. **Create a feature branch per task** — never commit directly to `main`
2. **Batch all changes for a task into one PR** — do not open a PR per commit
3. **Open as Draft PR if work is incremental** — get CI feedback without triggering a review
4. **Wait for CI to pass before requesting human review** — do not request review on a failing PR
5. **Address CI failures before pushing a new commit** — do not push workarounds; fix the root cause
6. **One task, one PR, one review cycle** — keeps the review queue manageable for the human

---

## Note on Future Repo Split

When frontend and backend are separated into independent repositories, each team maintains their own copy of this document, updated to reflect their specific CI checks and deploy pipeline. The principles — automated gates before human review, human review before merge, monitoring after deploy — remain the same.
