# ADR-0008: Monitor Skill Architecture — Layered Sub-skills + Structured Runbook

**Status:** Accepted
**Date:** 2026-04-16
**Relates to:** ADR-0005 (AI monitoring architecture), tasks 3.12 and 3.13

## Context

Task 3.12 initially shipped a single monolithic `/monitor-check` skill file
(317 lines, ~3000 tokens) containing all logic: live path, offline path, metric
diagnostics, fix steps, and downstream checks. Two problems surfaced during review:

1. **Context bloat:** The full file loads on every invocation regardless of which
   metric is breaching. When MCP tools are added in 3.13, all tool schemas would
   also load upfront — compounding the bloat.

2. **Duplication:** Diagnostic content (causes, fix steps) was embedded in the
   skill file and also existed in `docs/runbook.md`. Two places to maintain.

A secondary concern was raised: if sub-skills investigate layers in isolation,
how does the system identify cross-layer patterns (e.g. a deploy causing both
pool exhaustion and elevated error rates)?

## Decision

Replace the monolithic skill with a layered architecture:

### Layer 1 — Thin orchestrator (`monitor-check`)
~85 lines. Contains only:
- Config read and endpoint call
- Status table display
- Routing table (metric → sub-skill sequence)
- Synthesis step (cross-layer analysis after all sub-skills report)
- Pacing and tone rules

### Layer 2 — Focused sub-skills (one per infrastructure layer)
Each ~45–65 lines. Contains only investigation procedure for its layer:
- `monitor-server` — Render service status, recent deploys, git log
- `monitor-db` — /health endpoint, connection pool, slow query analysis
- `monitor-dependencies` — Resend and Twilio status pages and credential checks

Sub-skills load on demand based on the routing table — not upfront. A healthy
run loads only the orchestrator (~85 lines). A single-metric breach loads the
orchestrator + one sub-skill (~150 lines). Worst case (all metrics breaching)
loads all four files (~275 lines vs 317 today).

### Layer 3 — Structured per-metric runbook files
Sub-skills read `docs/runbook/{metric_name}.md` only after identifying the root
cause layer. Runbook files contain: metric definition, threshold, likely causes,
and fix steps — written for both human engineers and agents to read directly.

The metric name in the monitor API response maps directly to the runbook filename
(`error_rate` → `docs/runbook/error_rate.md`). No parsing required.

### Synthesis step
After all relevant sub-skills report, the orchestrator instructs Claude to review
all findings together and identify: timing correlations, causal chains, and
patterns spanning multiple layers before recommending any fix. Sub-skills operate
in isolation; Claude is the correlation engine across their outputs.

## Why not metric-based sub-skills?

Metric-based sub-skills (one per alert type) were considered. Rejected because:
- `error_rate` can be caused by web layer (bad deploy) OR DB layer (connection failure)
  — duplicating the DB checks in the error_rate sub-skill
- Layer-based maps directly to MCP tools (a DB tool, a Render tool), enabling
  clean reuse in 3.13 without restructuring

## MCP Bridge (Task 3.13)

The routing table in the orchestrator does not change when MCP arrives.
Each sub-skill swaps file reads for MCP tool calls:

| Sub-skill today | MCP tool in 3.13 |
|---|---|
| `git log --oneline -5` | `get_recent_commits()` |
| `GET /health` | `check_health_endpoint()` |
| Query `request_logs` | `query_metrics_table(metric, window)` |
| Fetch status pages | `check_provider_status(provider)` |
| Read runbook file | `get_runbook_entry(metric)` |

The synthesis step is identical — Claude holds all tool results in context
and reasons across them. MCP makes the investigation richer (structured data
vs prose), not structurally different.

## Consequences

- Typical invocation context drops from 317 lines to ~150 lines
- Runbook becomes dual-purpose: human-readable AND agent-readable
- Adding a new metric requires: one new runbook file + one routing table entry
  (no changes to existing sub-skills)
- Sub-skills are reusable across metrics (monitor-db used by both error_rate
  and p95_latency_ms paths)
- Cross-layer pattern detection is explicit (synthesis step) rather than implicit
- Migration of `docs/runbook.md` to per-file format is incremental — done
  alongside each new metric, not a big-bang rewrite
