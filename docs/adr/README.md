# Architecture Decision Records

Decisions made after the architecture doc was signed off (2026-04-06).
Each ADR records what changed, why, and what the consequences are.

| # | Title | Date | Status |
|---|---|---|---|
| [0001](0001-reservation-reminder-cron.md) | Reservation reminder cron — pg_cron + pg_net instead of cron-job.org | 2026-04-13 | Accepted |
| [0002](0002-request-observability.md) | Request observability — correlation IDs + request_logs table | 2026-04-14 | Accepted |
| [0003](0003-notification-observability.md) | Notification observability — notification_logs table | 2026-04-14 | Accepted |
| [0004](0004-log-retention.md) | Log retention — pg_cron 30-day auto-delete | 2026-04-14 | Accepted |
| [0005](0005-ai-monitoring-architecture.md) | AI monitoring agent — APScheduler + two-phase approach | 2026-04-14 | Accepted |
| [0006](0006-notifications-feature-flag.md) | Notifications feature flag | 2026-04-14 | Accepted |
| [0007](0007-monitoring-alert-channels.md) | Monitoring alert channels — GitHub Issues + email (not WhatsApp) | 2026-04-14 | Accepted |
