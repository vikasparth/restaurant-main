# ADR-0001: Reservation Reminder Cron — pg_cron + pg_net instead of cron-job.org

**Status:** Accepted
**Date:** 2026-04-13
**Supersedes:** Architecture doc section 15 ("Reservation reminder mechanism")

## Context

The original architecture specified cron-job.org (free external service) to ping
`POST /api/reservations/send-reminders` daily at 9am Pacific. During implementation
we evaluated this against Supabase's built-in pg_cron + pg_net extension combo.

## Decision

Use Supabase pg_cron to schedule the job and pg_net to make the HTTP POST to the
Render endpoint — no external cron service required.

Migration: `supabase/migrations/20260413000001_add_reminder_cron.sql`

Schedule: `0 17 * * *` (9am PDT, UTC-7). Change to `0 16 * * *` in PST (Nov–Mar).

Two Supabase config vars required:
- `app.api_base_url` — Render service URL
- `app.internal_token` — shared secret, same value as `INTERNAL_TOKEN` env var on Render

## Consequences

- One fewer external account to manage (no cron-job.org)
- pg_net must be enabled in Supabase dashboard (Extensions → pg_net)
- DST shift requires a manual SQL update twice a year (or accept 1h drift in off-season)
- **Not yet applied to production** — deferred until reservation reminder emails are enabled
