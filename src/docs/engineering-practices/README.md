# Engineering Practices — Frontend

**Scope:** Frontend engineers working in `src/` and the GraphQL gateway in `graphql-gateway/`.
**Last updated:** 2026-04-24

---

## Documents

| Document | What it covers |
|---|---|
| [ci-pipeline.md](ci-pipeline.md) | GitHub Actions CI workflow — what runs, how to investigate failures, branch protection setup |
| [pre-commit-hooks.md](pre-commit-hooks.md) | Husky and lint-staged — what runs locally on every commit, setup for new engineers |
| [graphql-guardrails.md](graphql-guardrails.md) | Schema validator and graphql-inspector — catching GraphQL drift before it reaches production |

---

## Related Shared Practices

| Document | Location |
|---|---|
| Branching strategy | [`docs/engineering-practices/branching-strategy.md`](../../../docs/engineering-practices/branching-strategy.md) |
| Full AI agent workflow | [`docs/engineering-practices/ai-agent-workflow.md`](../../../docs/engineering-practices/ai-agent-workflow.md) |

---

## Frontend Guardrail Summary

```mermaid
flowchart TD
    A[git commit] --> B{Pre-commit hook\nHusky + lint-staged}
    B -->|Lint or format fails| C[Commit rejected\nFix and retry]
    B -->|Passes| D[git push to feature branch]
    D --> E[PR opened on GitHub]
    E --> F{GitHub Actions CI}
    F --> G[npm run build\nTypeScript + Vite]
    F --> H[npm run lint\nESLint whole project]
    F --> I[npm test\nVitest]
    F --> J[Schema validator\nFuture 3.16.7]
    F --> K[graphql-inspector\nFuture 3.16.8]
    G & H & I --> L{All pass?}
    J & K --> L
    L -->|Any fail| M[PR blocked\nInvestigate in Actions tab]
    L -->|All pass| N[Human review]
    N -->|Approved| O[Merge to main]
```
