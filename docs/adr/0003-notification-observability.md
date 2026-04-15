# ADR-0003: Notification Observability — notification_logs Table

**Status:** Accepted
**Date:** 2026-04-14
**Adds to:** Architecture doc section 9 (Notification Flow)

## Context

Notification sends (Resend email, Twilio WhatsApp) could silently fail with no record.
The only signal was a log line in Render. There was no way to count failure rates,
identify which provider was degraded, or alert when failures crossed a threshold.

## Decision

Add a `notification_logs` table. Every send attempt (success or failure) writes one row:
`provider`, `channel`, `event_type`, `reference`, `success`, `error_code`.

Written fire-and-forget via `asyncio.create_task(_log_notification(...))` in
`services/notification_service.py` — does not block the HTTP response or affect
the customer if the log write itself fails.

Identified by `reference` (e.g. `AKR-20260414-0012`) — no customer PII stored.

Migration: `supabase/migrations/20260414000002_add_notification_logs.sql`

## Consequences

- Notification failure rate is now a queryable metric (feeds AI monitoring agent)
- No PII in the logs table — safe to query and expose via internal API
- `_log_notification` is mocked in tests to prevent connection pool exhaustion
  (fire-and-forget tasks + test teardown timing caused `MaxClientsInSessionMode` errors)
- When `NOTIFICATIONS_ENABLED=false`, no rows are written (no sends attempted = nothing to log)
