# ADR-0004: Log Retention — pg_cron 30-Day Auto-Delete

**Status:** Accepted
**Date:** 2026-04-14
**Applies to:** `request_logs`, `notification_logs`

## Context

Both observability tables grow unbounded with every request and notification send.
On Supabase free tier (500MB storage limit), unbounded growth would eventually fill
the database. A retention policy is required.

## Decision

Use pg_cron (already enabled for the reminder cron) to delete old rows nightly.

Scheduled in each table's migration file:
```sql
SELECT cron.schedule(
    'delete-old-request-logs',
    '0 3 * * *',
    $$DELETE FROM request_logs WHERE created_at < now() - INTERVAL '30 days'$$
);
```

Runs at 3am UTC daily. 30-day window retained.

## Consequences

- Storage stays bounded — safe on Supabase free tier
- 30-day window is sufficient for trend analysis and incident retrospectives
- No external service or code change required — runs inside Supabase automatically
- Longer retention requires upgrading Supabase tier or archiving to cold storage (not in scope)
