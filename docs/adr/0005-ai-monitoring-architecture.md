# ADR-0005: AI Monitoring Agent Architecture — APScheduler + Two-Phase Approach

**Status:** Accepted (Phase 1 in progress)
**Date:** 2026-04-14
**Adds to:** Architecture doc section 3 (Technology Stack)

## Context

The original architecture included UptimeRobot and GitHub Actions canary tests for
uptime and synthetic monitoring. These catch "server is down" and "endpoint broken"
scenarios but cannot detect degraded performance (high latency, elevated error rates,
notification failures) or perform root cause analysis.

## Decision

Build a two-phase AI monitoring agent:

### Phase 1 — Rule-based (task 3.11)
- APScheduler runs inside the Render FastAPI process — no external service
- Fires at 9:00 and 21:00 America/Los_Angeles (APScheduler handles DST)
- Queries `request_logs` and `notification_logs` for two consecutive 6-hour windows
- Alerts only if threshold breached in **both** windows (suppresses single-spike noise)
- Sends WhatsApp + email alert only when at least one metric is breaching (zero cost on healthy runs)
- All thresholds configurable via env vars (no code change to tune)
- Exposes `GET /api/internal/monitor` — metrics snapshot for Phase 2

### Phase 2 — Claude-driven via MCP (task 3.13)
- MCP server with tools: `query_metrics_table`, `check_endpoint`, `get_recent_errors`
- `/monitor-check` Claude Code Skill invokes the tools during a Pro session (no API billing)
- Claude drives its own investigation rather than reading a pre-packaged snapshot

## Consequences

- Phase 1: zero additional cost; alert fatigue reduced by two-window consecutive check
- Phase 2: zero API cost (covered by Claude Pro subscription)
- APScheduler restarts on Render deploy — acceptable given twice-daily schedule
- Twice-daily schedule chosen deliberately to stay well within Resend/Twilio free tier
- "No recent orders" metric excluded — low order volume during development would cause constant false alerts
