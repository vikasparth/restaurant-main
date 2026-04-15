import logging

from core.config import settings

logger = logging.getLogger(__name__)

def check_thresholds(snapshot: dict) -> list[str]:
    breaching = []

    # check error_rate
    er = snapshot["error_rate"]
    if er["window_1"] > settings.monitor_error_rate_threshold \
            and er["window_2"] > settings.monitor_error_rate_threshold:
        breaching.append("error_rate")

    # check p95_latency_threshold
    p95 = snapshot["p95_latency_ms"]
    if p95["window_1"] > settings.monitor_latency_p95_threshold_ms \
            and p95["window_2"] > settings.monitor_latency_p95_threshold_ms:
        breaching.append("p95_latency_ms")

    # check notification_failures
    nf = snapshot["notification_failures"]
    if nf["window_1"] > settings.monitor_notification_failure_threshold \
            and nf["window_2"] > settings.monitor_notification_failure_threshold:
        breaching.append("notification_failures") 
    return breaching

async def collect_snapshot(db, window_hours: int) -> dict:
    """Query DB for both windows. Returns raw metric values per window."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    window_1_start = now - timedelta(hours=window_hours)
    window_2_start = now - timedelta(hours=window_hours * 2)
    
    # --- error rate ---
    row = await db.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE status_code >= 500 AND created_at >= $1) AS err_w1,
            COUNT(*) FILTER (WHERE created_at >= $1)                        AS total_w1,
            COUNT(*) FILTER (WHERE status_code >= 500 AND created_at < $1)  AS err_w2,
            COUNT(*) FILTER (WHERE created_at < $1 AND created_at >= $2)    AS total_w2
        FROM request_logs
        WHERE created_at >= $2
        """,
        window_1_start,
        window_2_start,
    )
    error_rate_w1 = row["err_w1"] / row["total_w1"] if row["total_w1"] else 0.0
    error_rate_w2 = row["err_w2"] / row["total_w2"] if row["total_w2"] else 0.0
   
    # --- p95 latency ---
    rows = await db.fetch(
        """
        SELECT duration_ms, created_at
        FROM request_logs
        WHERE created_at >= $1
        ORDER BY duration_ms
        """,
        window_2_start,
    )
    w1_durations = [r["duration_ms"] for r in rows if r["created_at"] >= window_1_start]
    w2_durations = [r["duration_ms"] for r in rows if window_2_start <= r["created_at"] < window_1_start]

    # p95: sort is already applied by ORDER BY; find value at 95th percentile index
    def p95(values: list) -> int:
        if not values:
            return 0
        idx = int(len(values) * 0.95)
        return values[min(idx, len(values) - 1)]

    p95_w1 = p95(w1_durations)
    p95_w2 = p95(w2_durations)

    # --- notification failures ---
    notif_rows = await db.fetch(
        """
        SELECT success, created_at
        FROM notification_logs
        WHERE created_at >= $1
        """,
        window_2_start,
    )
    # count failed sends (success=False) in each window
    notif_failures_w1 = sum(
        1 for r in notif_rows
        if not r["success"] and r["created_at"] >= window_1_start
    )
    notif_failures_w2 = sum(
        1 for r in notif_rows
        if not r["success"] and r["created_at"] < window_1_start
    )

    return {
        "error_rate": {
            "window_1": error_rate_w1,
            "window_2": error_rate_w2,
        },
        "p95_latency_ms": {
            "window_1": p95_w1,
            "window_2": p95_w2,
        },
        "notification_failures": {
            "window_1": notif_failures_w1,
            "window_2": notif_failures_w2,
        },
    }
