import pytest
from unittest.mock import AsyncMock, patch

from services.monitor_service import check_thresholds, run_monitor

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
        "error_rate": {"window_1": error_rate_w1, "window_2": error_rate_w2},
        "p95_latency_ms": {"window_1": p95_latency_w1, "window_2": p95_latency_w2},
        "notification_failures": {
            "window_1": notif_failures_w1,
            "window_2": notif_failures_w2,
        },
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
        error_rate_w1=0.08,
        error_rate_w2=0.07,
        p95_latency_w1=2400,
        p95_latency_w2=2200,
        notif_failures_w1=3,
        notif_failures_w2=4,
    )
    result = check_thresholds(snapshot)
    assert "error_rate" in result
    assert "p95_latency_ms" in result
    assert "notification_failures" in result


# ---------------------------------------------------------------------------
# run_monitor — orchestration logic
# ---------------------------------------------------------------------------


# When metrics breach, GitHub issue is opened and owner email is sent
@pytest.mark.asyncio
async def test_run_monitor_breaching_opens_issue_and_sends_email():
    snapshot = make_snapshot(error_rate_w1=0.08, error_rate_w2=0.07)
    breaching = ["error_rate"]

    with patch(
        "services.monitor_service.open_or_update_github_issue",
        AsyncMock(return_value="https://github.com/issues/1"),
    ) as mock_open, patch(
        "services.monitor_service.send_email", AsyncMock()
    ) as mock_email, patch(
        "services.monitor_service.close_github_issue", AsyncMock()
    ) as mock_close:

        await run_monitor(breaching, snapshot)

        mock_open.assert_called_once()
        mock_email.assert_called_once()
        mock_close.assert_not_called()


# When all metrics are healthy, open issue is closed and no email is sent
@pytest.mark.asyncio
async def test_run_monitor_healthy_closes_issue_and_skips_email():
    snapshot = make_snapshot()  # all zeros — all healthy
    breaching = []

    with patch(
        "services.monitor_service.close_github_issue", AsyncMock()
    ) as mock_close, patch(
        "services.monitor_service.send_email", AsyncMock()
    ) as mock_email, patch(
        "services.monitor_service.open_or_update_github_issue", AsyncMock()
    ) as mock_open:

        await run_monitor(breaching, snapshot)

        mock_close.assert_called_once()
        mock_email.assert_not_called()
        mock_open.assert_not_called()


# When GitHub call fails, run_monitor logs and returns cleanly
@pytest.mark.asyncio
async def test_run_monitor_github_failure_returns_cleanly():
    snapshot = make_snapshot(error_rate_w1=0.08, error_rate_w2=0.07)
    breaching = ["error_rate"]

    with patch(
        "services.monitor_service.open_or_update_github_issue",
        AsyncMock(side_effect=Exception("GitHub down")),
    ) as mock_open, patch(
        "services.monitor_service.send_email", AsyncMock()
    ) as mock_email:

        await run_monitor(breaching, snapshot)  # must not raise

        mock_open.assert_called_once()
        mock_email.assert_not_called()
