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

# All metrics below threshold — nothing to alert on
def test_all_healthy_returns_no_alerts():
    snapshot = make_snapshot()
    result = check_thresholds(snapshot)
    assert result == []

# Error rate above 5% in both windows — should be flagged
def test_error_rate_breaching_both_windows_returns_alert():
    snapshot = make_snapshot(error_rate_w1=0.08, error_rate_w2=0.07)
    result = check_thresholds(snapshot)
    assert "error_rate" in result

# Spike in window 1 only — not sustained, should be suppressed
def test_error_rate_breaching_one_window_only_no_alert():
    snapshot = make_snapshot(error_rate_w1=0.08, error_rate_w2=0.01)
    result = check_thresholds(snapshot)
    assert "error_rate" not in result

# p95 latency above 2000ms in both windows — should be flagged
def test_latency_breaching_both_windows_returns_alert():
    snapshot = make_snapshot(p95_latency_w1=2400, p95_latency_w2=2200)
    result = check_thresholds(snapshot)
    assert "p95_latency_ms" in result


# Latency spike in window 1 only — not sustained, should be suppressed
def test_latency_breaching_one_window_only_no_alert():
    snapshot = make_snapshot(p95_latency_w1=2400, p95_latency_w2=1800)
    result = check_thresholds(snapshot)
    assert "p95_latency_ms" not in result

# Notification failures above 2 in both windows — should be flagged
def test_notification_failures_breaching_both_windows_returns_alert():
    snapshot = make_snapshot(notif_failures_w1=3, notif_failures_w2=4)
    result = check_thresholds(snapshot)
    assert "notification_failures" in result


# Notification failures in window 1 only — not sustained, should be suppressed
def test_notification_failures_breaching_one_window_only_no_alert():
    snapshot = make_snapshot(notif_failures_w1=3, notif_failures_w2=0)
    result = check_thresholds(snapshot)
    assert "notification_failures" not in result

# Multiple metrics breaching in both windows — all should appear in result
def test_multiple_metrics_breaching_returns_all_alerts():
    snapshot = make_snapshot(
        error_rate_w1=0.08, error_rate_w2=0.07,
        p95_latency_w1=2400, p95_latency_w2=2200,
        notif_failures_w1=3, notif_failures_w2=4,
    )
    result = check_thresholds(snapshot)
    assert "error_rate" in result
    assert "p95_latency_ms" in result
    assert "notification_failures" in result
