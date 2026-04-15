# ADR-0007: Monitoring Alert Channels — GitHub Issues + Email (not WhatsApp)

**Status:** Accepted
**Date:** 2026-04-14
**Supersedes:** ADR-0005 (alert channel section only)

## Context

ADR-0005 specified WhatsApp + email as the alert channels for the monitoring agent.
WhatsApp uses Twilio (variable cost per message) and produces no persistent record
of past incidents. We needed a primary record system with full incident history.

## Decision

- **Primary:** GitHub Issues — opened automatically on breach, closed automatically on recovery
  - Free, unlimited, already on GitHub
  - Label `monitoring-alert` used to find open alerts programmatically
  - Full incident history preserved in the repo
- **Secondary:** Owner email — sent on breach only, includes link to the GitHub Issue
- **Removed:** WhatsApp — not used for monitoring (eliminates Twilio dependency entirely from monitoring)

Two new config fields: `GITHUB_TOKEN` (personal access token, issues:write scope) and
`GITHUB_REPO` (e.g. `vikasparth/restaurant-main`).

## Consequences

- Zero variable cost for monitoring alerts (GitHub free, Resend free tier sufficient)
- Incidents have a permanent searchable audit trail in GitHub
- Auto-close on recovery means the issue list reflects current system health
- Requires a GitHub personal access token on Render — one new env var
- If GitHub API is unreachable, alert silently fails — acceptable for a learning project
