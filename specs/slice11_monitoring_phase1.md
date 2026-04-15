# Spec — Slice 11: AI Monitoring Agent Phase 1 (Rule-Based)

## Goal
A scheduled background job that checks three key health metrics twice daily and fires a
WhatsApp + email alert only when a problem is sustained across two consecutive windows
(not a single spike). An internal endpoint exposes the same snapshot for Phase 2 (Skill).

---

## Schedule
- **Times:** 9:00 and 21:00 `America/Los_Angeles` (APScheduler handles PDT/PST shift)
- **Runs inside:** the Render FastAPI process via APScheduler — no external service needed

---

## Metrics

Each metric is evaluated over **two consecutive windows** of `MONITOR_WINDOW_HOURS` (default 6h).

| Name | Window 1 | Window 2 | Alert condition |
|---|---|---|---|
| `error_rate` | last 6h | prior 6h (6–12h ago) | breached in both windows |
| `p95_latency_ms` | last 6h | prior 6h | breached in both windows |
| `notification_failures` | last 6h | prior 6h | breached in both windows |

**Alert fires only if at least one metric breaches in both windows.** A single-window spike → no alert.

---

## Thresholds (all configurable via env vars)

| Config field | Env var | Default | Unit |
|---|---|---|---|
| `monitor_window_hours` | `MONITOR_WINDOW_HOURS` | `6` | hours |
| `monitor_error_rate_threshold` | `MONITOR_ERROR_RATE_THRESHOLD` | `0.05` | fraction (5%) |
| `monitor_latency_p95_threshold_ms` | `MONITOR_LATENCY_P95_THRESHOLD_MS` | `2000` | milliseconds |
| `monitor_notification_failure_threshold` | `MONITOR_NOTIFICATION_FAILURE_THRESHOLD` | `2` | count |

---

## Data sources

| Metric | Table | Key columns |
|---|---|---|
| Error rate | `request_logs` | `status_code`, `created_at` |
| p95 latency | `request_logs` | `duration_ms`, `created_at` |
| Notification failures | `notification_logs` | `success`, `created_at`, `provider` |

> **Note:** `notification_failures` only alerts on rows that were attempted and failed.
> When `NOTIFICATIONS_ENABLED=false`, no sends are attempted → no rows written → metric stays 0 → no false alert.

---

## Alert format

Sent via WhatsApp (owner) + email (owner). Only sent if at least one metric is breaching.

```
[ALERT] Aap ki Rasoi — 2 issues detected

• Error rate: 8.2% in both windows (threshold: 5%)
• p95 latency: 2400ms in both windows (threshold: 2000ms)

Checked at: 2026-04-14 21:00 Pacific
```

If all metrics are healthy → no message sent (zero WhatsApp/email cost).

---

## Internal endpoint

`GET /api/internal/monitor`

Protected by `X-Internal-Token` header (same as `/send-reminders`).

Response shape:
```json
{
  "checked_at": "2026-04-14T21:00:00",
  "window_hours": 6,
  "metrics": {
    "error_rate": {
      "window_1": 0.082,
      "window_2": 0.071,
      "threshold": 0.05,
      "breaching": true
    },
    "p95_latency_ms": {
      "window_1": 2400,
      "window_2": 1800,
      "threshold": 2000,
      "breaching": false
    },
    "notification_failures": {
      "window_1": 1,
      "window_2": 0,
      "threshold": 2,
      "breaching": false
    }
  },
  "alerts_fired": true
}
```

`breaching: true` means threshold exceeded in **both** windows.

---

## Files

| File | Action |
|---|---|
| `backend/services/monitor_service.py` | New — `collect_snapshot()`, `check_thresholds()`, `run_monitor()` |
| `backend/routers/internal.py` | Add `GET /api/internal/monitor` |
| `backend/core/scheduler.py` | New — APScheduler instance, registers monitor job |
| `backend/core/config.py` | Add 4 monitor config fields |
| `backend/main.py` | Start/stop scheduler on app lifespan |
| `backend/tests/test_monitor.py` | New — unit tests for each threshold check |
| `docs/runbook.md` | Add entries for error_rate, p95_latency, notification_failures |

---

## Function signatures

```python
# monitor_service.py

async def collect_snapshot(db, window_hours: int) -> dict:
    """Query DB for both windows. Returns raw metric values per window."""

async def check_thresholds(snapshot: dict) -> list[dict]:
    """Compare snapshot values against settings thresholds.
    Returns list of breaching metrics (empty list = all healthy)."""

async def run_monitor(db) -> None:
    """Collect snapshot, check thresholds, fire alerts if needed. Never raises."""
```

---

## Out of scope for this slice
- No Claude API calls (Phase 2)
- No MCP tools (Phase 3)
- No per-endpoint breakdown — aggregate metrics only
- No memory/CPU metrics (Render dashboard covers those)
