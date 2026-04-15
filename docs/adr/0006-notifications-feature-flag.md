# ADR-0006: Notifications Feature Flag

**Status:** Accepted
**Date:** 2026-04-14
**Adds to:** Architecture doc section 9 (Notification Flow)

## Context

During development and early production, sending real emails and WhatsApp messages
on every test order/reservation creates noise and consumes free tier quota. A way
to disable all outbound sends without code changes was needed.

## Decision

Add `NOTIFICATIONS_ENABLED` boolean env var to `Settings` in `core/config.py`.

All four notification functions (`notify_order`, `notify_reservation`, `notify_catering`,
`send_reservation_reminders`) return immediately if `settings.notifications_enabled` is `False`.

Default: `True` in production, `False` in development (set via `.env`).

## Consequences

- No emails or WhatsApp sent when flag is off — free tier quota preserved during development
- When flag is off, `notification_logs` receives no rows (no sends attempted)
- The AI monitoring agent's notification failure metric correctly reads 0 when flag is off
  (not a false alarm — silence means "nothing attempted", not "everything failed")
- Flag is per-deployment — toggled via Render env var, no code deploy required
