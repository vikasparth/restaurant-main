from unittest.mock import patch
from agents.sentry_utils import record_agent_run

COMPLETED_HIGH = {"status": "completed", "confidence": "high"}
PARTIAL_LOW = {"status": "partial", "confidence": "low"}


def test_record_agent_run_completed():
    usage = [
        {"input_tokens": 900, "output_tokens": 120},
        {"input_tokens": 780, "output_tokens": 192},
    ]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        record_agent_run("frontend-sentry", COMPLETED_HIGH, usage)

        mock_sentry.init.assert_called_once()
        mock_sentry.capture_event.assert_called_once()
        event = mock_sentry.capture_event.call_args[0][0]
        assert event["tags"]["agent"] == "frontend-sentry"
        assert event["tags"]["status"] == "completed"
        assert event["extra"]["input_tokens"] == 1680
        assert event["extra"]["output_tokens"] == 312
        assert event["extra"]["total_tokens"] == 1992
        assert event["extra"]["turns_used"] == 2
        assert event["extra"]["confidence_numeric"] == 3


def test_record_agent_run_partial():
    usage = [{"input_tokens": 500, "output_tokens": 80}]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        record_agent_run("frontend-sentry", PARTIAL_LOW, usage)

        event = mock_sentry.capture_event.call_args[0][0]
        assert event["tags"]["status"] == "partial"
        assert event["extra"]["confidence_numeric"] == 1


def test_record_agent_run_no_dsn():
    usage = [{"input_tokens": 500, "output_tokens": 80}]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        with patch("agents.sentry_utils.AGENTS_SENTRY_DSN", ""):
            record_agent_run("frontend-sentry", COMPLETED_HIGH, usage)
            mock_sentry.init.assert_not_called()


def test_confidence_numeric_mapping():
    from agents.sentry_utils import confidence_to_numeric

    assert confidence_to_numeric("high") == 3
    assert confidence_to_numeric("medium") == 2
    assert confidence_to_numeric("low") == 1
    assert confidence_to_numeric("missing") == 0


# why: issue_number groups all agents from one investigation — without this tag,
# you cannot filter Sentry to "show me every agent that ran for issue #47"
def test_record_agent_run_issue_number_tag():
    usage = [{"input_tokens": 900, "output_tokens": 120, "cache_read_input_tokens": 500, "cache_creation_input_tokens": 100}]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        record_agent_run("backend-sentry", COMPLETED_HIGH, usage, issue_number="123")

        event = mock_sentry.capture_event.call_args[0][0]
        assert event["tags"]["issue_number"] == "123"


# why: usage_by_turn must be preserved as a raw list, not just summed — summing
# hides which turn caused a token spike; the raw list enables per-turn drill-down in Sentry
def test_record_agent_run_usage_by_turn_preserved():
    usage = [
        {"input_tokens": 300, "output_tokens": 50, "cache_read_input_tokens": 200, "cache_creation_input_tokens": 0},
        {"input_tokens": 400, "output_tokens": 80, "cache_read_input_tokens": 300, "cache_creation_input_tokens": 0},
        {"input_tokens": 500, "output_tokens": 100, "cache_read_input_tokens": 400, "cache_creation_input_tokens": 0},
    ]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        record_agent_run("backend-sentry", COMPLETED_HIGH, usage)

        event = mock_sentry.capture_event.call_args[0][0]
        assert event["extra"]["usage_by_turn"] == usage
