# Runbook Index — Aap ki Rasoi

> Per-metric runbook files are the source of truth for alert diagnosis and fixes.
> The legacy `docs/runbook.md` file contains earlier entries (1–12) not yet migrated.

## Monitored Metrics

| Metric | Threshold | Runbook |
|---|---|---|
| error_rate | > 5% in both windows | [error_rate.md](error_rate.md) |
| p95_latency_ms | > 2000ms in both windows | [p95_latency_ms.md](p95_latency_ms.md) |
| notification_failures | > 2 per window in both windows | [notification_failures.md](notification_failures.md) |

## Other Entries (in docs/runbook.md)

| Entry | Topic |
|---|---|
| 1 | Memory utilization — upward trend |
| 2 | CPU utilization — upward or spiky trend |
| 12 | Downstream dependency failures (Supabase, Resend, Twilio) |

## How to use

1. Receive an alert (email / GitHub Issue)
2. Run `/monitor-check` in Claude Code for guided diagnosis
3. Or find the matching runbook file above and follow the fix steps directly
4. Verify the metric recovers — alerts close automatically
