# ADR-0009: GraphQL Inspector CI — Double Checkout Instead of Official GitHub Action

**Status:** Accepted
**Date:** 2026-04-25
**Relates to:** Execution plan item 3.16.8

## Context

`graphql-inspector` is an open-source tool by The Guild that detects breaking GraphQL schema changes by comparing two versions of a schema. It is used as a CI step on every PR to prevent breaking changes from reaching production.

The tool provides two integration paths for GitHub Actions:

1. **Official GitHub Action** (`kamilkisiela/graphql-inspector@master`) — a pre-built Action with GitHub Checks API integration and inline PR annotations.
2. **CLI** (`@graphql-inspector/cli`) — the underlying npm package, usable in a `run:` step.

## Decision

We use the **CLI via a double-checkout pattern** instead of the official GitHub Action.

The CI step:
```yaml
- name: Checkout main branch for schema comparison
  uses: actions/checkout@v4
  with:
    ref: main
    path: temp-main

- name: Check for breaking GraphQL schema changes
  run: |
    npx @graphql-inspector/cli diff \
      "temp-main/graphql-gateway/schemas/**/*.graphql" \
      "graphql-gateway/schemas/**/*.graphql"
```

## Reasons

**The official Action does not support glob patterns.**
The `schema:` input of the GitHub Action requires an explicit file path — it cannot resolve `graphql-gateway/schemas/**/*.graphql`. This is a known limitation tracked in [issue #1978](https://github.com/kamilkisiela/graphql-inspector/issues/1978), opened in 2021 and still unresolved.

Without glob support, every new GraphQL schema file (`orders.graphql`, `catering.graphql`) would require a new `uses:` entry in `ci.yml` — a manual CI change for each domain migration.

**The double-checkout pattern solves the glob limitation cleanly.**
By checking out `main` into `temp-main/`, both schema versions are available as local filesystem paths. The CLI resolves glob patterns against local paths natively. New schema files are picked up automatically — no CI change needed when adding new domains.

**The CLI is more actively maintained than the Action.**
The GitHub Action has seen minimal development compared to the CLI package. Relying on the CLI directly reduces dependency on a less-maintained integration layer.

## Trade-offs

| | Official Action | Double checkout + CLI |
|---|---|---|
| Inline PR annotations | ✅ Yes | ❌ No |
| Glob pattern support | ❌ No | ✅ Yes |
| Auto-picks up new schemas | ❌ No | ✅ Yes |
| Maintenance risk | Higher (Action lags CLI) | Lower |

The loss of inline PR annotations is acceptable — CI failure output in the Actions log is sufficient for this team's workflow.

## Consequences

- New GraphQL schema files are automatically validated without any CI changes.
- When the official Action adds glob support, we can migrate back — the switch is a straightforward ci.yml change.
- `temp-main/` is created in the CI workspace during the job and discarded when the runner is cleaned up.
