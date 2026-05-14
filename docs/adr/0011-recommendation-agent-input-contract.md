# ADR-0011: Recommendation Agent Input Contract — Codebase Findings Drive the Fix, Extractors Enrich Context

**Status:** Accepted
**Date:** 2026-05-13
**Architecture doc section:** `Recommendation Agent`

## Context

When designing the Recommendation Agent (D.6), a question arose: should it receive
the full combined payload from all extractors, or only the Codebase Agent findings?

The Codebase Agent already returns a structured root cause analysis (~50 tokens):
`root_cause_file`, `fix_location`, `fix_type`, `fix_detail`. If we trust that
analysis, the Recommendation Agent only needs those fields to write the code change.

However the Recommendation Agent also produces cross-source context — regression flag,
confidence score, severity, affected endpoint — that cannot be derived from the
codebase alone. That context requires data from the other extractors.

## Decision

The Recommendation Agent receives the **combined payload from all extractors**
(Sentry frontend, Sentry backend, Render Logs, GitHub, Codebase Agent findings),
but each source plays a distinct role:

| Source | Role in Recommendation Agent |
|---|---|
| Codebase Agent | **Drives the fix** — `fix_location`, `fix_type`, `fix_detail` determine what code change goes into the PR |
| Sentry (frontend + backend) | **Enriches severity and impact** — `user_count`, `error_count`, `first_seen` inform confidence score and PR description |
| Render Logs | **Enriches endpoint context** — `path`, `status`, `error_count` confirm which endpoint is affected |
| GitHub | **Enriches regression context** — `pr_merged_at` vs Sentry `first_seen` determines regression flag; `files_changed` cross-referenced with Sentry `top_frames` informs confidence |

The Recommendation Agent's system prompt must be structured to use Codebase findings
as the primary signal for the code change, and all other extractor data as enrichment
for the PR description, confidence scoring, and regression determination.

## Troubleshooting Sequence

The Recommendation Agent follows this reasoning order when synthesising findings:

1. **Regression check** — compare Sentry `first_seen` vs GitHub `pr_merged_at`. If
   `first_seen` predates the last deployment → not a regression → set
   `regression_flag: false`, lower confidence.
2. **File overlap check** — compare Sentry `top_frames` files vs GitHub
   `files_changed`. Direct overlap → high confidence regression. No overlap →
   indirect regression or pre-existing bug.
3. **Severity check** — use Sentry `user_count` and Render `error_count` to set
   impact level (high / medium / low).
4. **Fix derivation** — use Codebase Agent `fix_location`, `fix_type`, `fix_detail`
   to write the code change. This is the only source for the actual fix — never
   derive the fix from Sentry or Render data alone.
5. **Confidence scoring** — combine regression flag, file overlap, and severity into
   a single numeric confidence score (high=3, medium=2, low=1).

## Alternatives Considered

**Send only Codebase Agent findings:** Simpler and cheaper (~50 tokens). Rejected
because the Recommendation Agent cannot determine regression flag, confidence, or
write a meaningful PR description without knowing severity, affected endpoint, and
deployment context. A PR with no impact context is less useful for human review.

**Send everything but let Claude decide how to use it:** No structured guidance.
Rejected because it produces inconsistent reasoning across runs — Claude may
weight sources differently on each invocation. Explicit roles per source make the
output deterministic and testable.

## Consequences

- **Recommendation Agent prompt** must have an explicit section for each source role
  (fix driver vs context enrichment) — not a flat combined payload dump
- **D.4 GitHub extractor** must return `pr_merged_at` and `files_changed` — both
  are required for the regression check and file overlap check
- **D.5 Codebase Agent** must return `fix_location`, `fix_type`, `fix_detail` — the
  Recommendation Agent depends on these fields to write the code change
- **D.6 spec** must include the troubleshooting sequence above as acceptance criteria
