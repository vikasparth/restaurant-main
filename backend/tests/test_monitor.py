import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from services.monitor_service import check_thresholds, collect_snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_snapshot(
    error_rate_w1=0.0,
    error_rate_w2=0.0,
    p95_latency_w1=0,
    p95_latency_w2=0,
    notif_failures_w1=0,
    notif_failures_w2=0,
):
    """Build a snapshot dict with the same shape collect_snapshot() returns."""
    return {
        "error_rate":            {"window_1": error_rate_w1, "window_2": error_rate_w2},
        "p95_latency_ms":        {"window_1": p95_latency_w1, "window_2": p95_latency_w2},
        "notification_failures": {"window_1": notif_failures_w1, "window_2": notif_failures_w2},
    }


# ---------------------------------------------------------------------------
# check_thresholds — pure logic, no DB
# ---------------------------------------------------------------------------
