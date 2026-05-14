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
| [0008](0008-monitor-skill-architecture.md) | Monitor skill architecture — layered sub-skills + structured runbook | 2026-04-16 | Accepted |
| [0009](0009-graphql-inspector-ci-approach.md) | GraphQL Inspector CI — double checkout instead of official GitHub Action | 2026-04-25 | Accepted |
| [0010](0010-specialized-agent-architecture.md) | Specialized agent architecture — least privilege + orchestration layer | 2026-04-28 | Accepted |
| [0011](0011-recommendation-agent-input-contract.md) | Recommendation Agent input contract — Codebase findings drive fix, extractors enrich context | 2026-05-13 | Accepted |
