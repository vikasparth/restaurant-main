# ADR-0002: Request Observability — Correlation IDs + request_logs Table

**Status:** Accepted
**Date:** 2026-04-14
**Adds to:** Architecture doc section 11 (Logging Strategy)

## Context

The original logging strategy wrote application logs to Render (stdout) only. There was
no way to correlate a specific request across log lines, or to query request volume,
error rates, or latency trends programmatically. This blocked the AI monitoring agent
(task 3.11) which needs queryable metrics.

## Decision

Two additions:

**1. Correlation ID middleware** (`backend/core/middleware.py`)
- `RequestLoggingMiddleware` generates a UUID (`request_id`) per request
- Stored in a `contextvars.ContextVar` — isolated per async task, no race conditions
- `RequestIdFilter` in `core/logging.py` stamps `request_id` on every log line automatically
- Result: one `request_id` search in Render finds all log lines for that request

**2. `request_logs` DB table**
- Every request written to DB: `method`, `path`, `status_code`, `duration_ms`, `request_id`
- Written fire-and-forget via `asyncio.create_task` — does not block HTTP response
- Migration: `supabase/migrations/20260414000001_add_request_logs.sql`

## Consequences

- Metrics (error rate, latency p95, request count) are now queryable from Python
- Render logs and DB rows are linked via `request_id` — full trace possible
- Query parameters are never logged (PII risk)
- Request bodies and headers are never logged in middleware (PII risk)
- Small DB write overhead per request (~negligible on free tier)
