# Engineering Practices — Shared

**Scope:** Repository-level practices that apply to all engineers and AI agents today.

**Note on future repo split:** When frontend and backend are separated into independent repositories, each team copies the documents they need from this folder and maintains their own version. See [`docs/phase2/two-team-ownership.md`](../phase2/two-team-ownership.md) for the split plan.

---

## Guardrail Chain — Development to Production

Every change passes through five layers of automated and human checks before reaching production.

```mermaid
flowchart LR
    A[Write Code] --> B[Pre-commit\nHusky / pre-commit]
    B --> C[Feature Branch\nPR opened]
    C --> D[CI Pipeline\nGitHub Actions]
    D --> E[Human Review]
    E --> F[Merge to main]
    F --> G[Deploy]
    G --> H[Canary + Sentry\nProduction monitoring]

    style B fill:#dbeafe,stroke:#3b82f6
    style D fill:#dcfce7,stroke:#22c55e
    style E fill:#fef9c3,stroke:#eab308
    style H fill:#fce7f3,stroke:#ec4899
```

| Layer | Catches | Can be skipped? |
|---|---|---|
| Pre-commit | Lint and format errors on staged files | Yes — `--no-verify` (discouraged) |
| CI Pipeline | Type errors, build failures, test failures, schema drift | No |
| Human review | Intent, logic, design problems no tool can detect | No (branch protection) |
| Canary + Sentry | Runtime failures in production | N/A — always running |

---

## Documents in This Folder

| Document | What it covers |
|---|---|
| [branching-strategy.md](branching-strategy.md) | Feature branch workflow, naming, draft PRs, commit batching, branch protection rules |
| [ai-agent-workflow.md](ai-agent-workflow.md) | Full development-to-production sequence diagram with all guardrail layers |

---

## Team-Specific Practices

| Team | Location |
|---|---|
| Frontend | [`src/docs/engineering-practices/`](../../src/docs/engineering-practices/) |
| Backend | [`backend/docs/engineering-practices/`](../../backend/docs/engineering-practices/) |
