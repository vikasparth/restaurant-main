# GraphQL Gateway Layer
**Status:** ⏳ Pending — task 3.16 in execution-plan.md

## Repository Structure

Frontend (`src/`) and backend (`backend/`) both live in the same repository (`main_project`). The frontend was originally built in Lovable and migrated into `main_project`, which is now the single source of truth for both.

When this document refers to "frontend" it means `src/` and when it refers to "backend" it means `backend/`. Ownership is a team responsibility, not a repo boundary.

**Future separation:** The code boundary is already clean — no cross-directory imports, separate package managers (npm and pip), and deployments already go to separate hosts (Vercel for frontend, Render for backend). Separating into two repos in the future is feasible with a `git filter-repo` split and would require splitting shared docs and skills. New backend-specific docs should be kept in `backend/docs/` to make a future split easier.

---

## Ownership Model (decided)

- Backend team owns `backend/` (Python + REST API + `openapi.json`) — they never write GraphQL code
- Frontend team owns `src/` (React + GraphQL gateway) — they never modify Python
- GraphQL is a **frontend-side translation layer** that sits in front of the REST API, not a replacement for it
- The REST API remains the canonical interface for all callers — programmatic users, third-party integrations, and the GraphQL gateway all consume it

**Why this split:** Backend team writes APIs for multiple consumers. Forcing them to adopt GraphQL types would couple their design to one consumer's preferences. The gateway pattern gives the frontend team full GraphQL control without imposing any cost on the backend team.

---

## How It Works

```
React app → GraphQL gateway (src/) → REST API (backend/) → Database
```

The gateway calls backend REST endpoints and exposes a GraphQL interface to React. `openapi.json` is the contract the gateway is built against — if the backend changes it, the gateway breaks in CI.

**Cost:** Free — Apollo Server or GraphQL Mesh are open source. No new infrastructure needed. Engineering time only.

---

## Contract Validation — Two Independent Canary Layers

| Layer | Canary | What it catches |
|---|---|---|
| Backend REST | Existing `backend/tests/canary/` — pytest hitting live REST endpoints | Backend crashed, endpoint broken, DB down |
| GraphQL gateway | New GraphQL layer canaries in `src/` — GraphQL queries hitting live gateway | Gateway resolver broken, REST contract changed under it, field mapping wrong |

If a backend canary fails — backend team's problem. If a GraphQL canary fails — frontend team investigates first (could be their resolver, could be backend changed something under them).

**Additional contract tooling:**
- `schema.graphql` lives in `src/` — auto-generated from gateway resolver types, committed as a snapshot
- `graphql-codegen` generates TypeScript types from `schema.graphql` — frontend build fails if a React query references a non-existent field
- `graphql-inspector` runs in CI — breaks on breaking schema changes between PRs; validates `schema.graphql` against its own committed history to prevent accidental breaking changes to React consumers
- `openapi-diff` runs in CI — detects breaking REST changes and notifies the frontend team (does not fail the pipeline — backend should not be blocked by frontend concerns)

---

## Observability Across All Three Layers

| Layer | Runs on | Error logging | Gap without it |
|---|---|---|---|
| React | Browser | Sentry React SDK | Browser crashes and query errors invisible |
| GraphQL gateway | Vercel (Node.js) | Sentry Node.js SDK — must be added from day one | Resolver crashes invisible — you'd know React got an error and backend got a request, but what happened inside the gateway is a black box |
| Backend REST | Render (Python) | `request_logs` table + Sentry backend SDK (task 3.14) | Already covered |

**Prerequisite before going live with the gateway:** Sentry Node.js SDK must be installed in the gateway from day one. Without it the middle layer is entirely dark.

---

## Schema Validation — Coding Time and Runtime

| When | What validates | What it catches |
|---|---|---|
| Coding session | Claude Code reads `openapi.json` + `schema.graphql` before writing any resolver | Field mapping mismatches caught before code is committed |
| Build time | `graphql-codegen` generates TypeScript types from `schema.graphql` | React query references a non-existent field — build fails |
| PR / CI | `graphql-inspector` compares new vs committed `schema.graphql` | Breaking schema changes introduced between PRs |
| Runtime | GraphQL layer canaries — scheduled queries against live gateway + backend | Backend changed contract under the gateway, resolver returns null, intermittent failures |

---

## What Changes — Frontend (`src/`)

- [ ] Add GraphQL gateway (Apollo Server or GraphQL Mesh) inside `src/` — resolvers call backend REST endpoints via `openapi.json` contract
- [ ] **Add Sentry Node.js SDK to the gateway from day one** — captures resolver crashes, failed REST calls, and which GraphQL query triggered them
- [ ] Define `schema.graphql` in `src/` — auto-generated from gateway types, committed as the stable reference
- [ ] Add `graphql-codegen` to build — TypeScript types generated from `schema.graphql`; build fails on schema mismatch
- [ ] Add `graphql-inspector` to CI — breaks on breaking schema changes between PRs
- [ ] Add GraphQL layer canaries — scheduled GraphQL queries against live gateway; alert on failure
- [ ] Update `src/CLAUDE.md` with two rules for Claude Code:
  1. Never hand-write TypeScript types for API responses — always import from `__generated__/types`
  2. Before writing or modifying any gateway resolver, read `openapi.json` and `schema.graphql` and verify field mapping is consistent — flag any mismatch before writing code
- [ ] All React data fetching goes through the GraphQL gateway — never call backend REST endpoints directly from React components

## What Changes — Backend (`backend/`)

- [ ] Add `openapi-diff` to CI — detects breaking REST changes; output is a notification to frontend team, not a pipeline failure
- [ ] Add rule to `backend/CLAUDE.md`: any change to a public endpoint shape, field name, or status code requires regenerating `openapi.json` before merging
