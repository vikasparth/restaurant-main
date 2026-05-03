import pytest
from unittest.mock import patch, MagicMock
from agents.sentry_utils import record_agent_run
import agents.config as config

COMPLETED_HIGH_YAML = """\
metadata:
  agent: frontend-sentry
  status: completed
  confidence: high
"""
def test_record_agent_run_completed():
    usage = [
        {"input_tokens": 900, "output_tokens": 120},
        {"input_tokens": 780, "output_tokens": 192},
    ]
    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        mock_transaction = MagicMock()
        mock_sentry.start_transaction.return_value.__enter__ = MagicMock(return_value=mock_transaction)
        mock_sentry.start_transaction.return_value.__exit__ = MagicMock(return_value=False)

        record_agent_run("frontend-sentry", COMPLETED_HIGH_YAML, usage)

        mock_sentry.init.assert_called_once()
        mock_sentry.start_transaction.assert_called_once_with(
            name="agent.run", sampled=True
        )
        mock_transaction.set_tag.assert_called_once_with("agent", "frontend-sentry")
        mock_transaction.set_data.assert_any_call("input_tokens", 1680)
        mock_transaction.set_data.assert_any_call("output_tokens", 312)
        mock_transaction.set_data.assert_any_call("total_tokens", 1992)
        mock_transaction.set_data.assert_any_call("turns_used", 2)
        mock_transaction.set_data.assert_any_call("confidence_numeric", 3)

        assert mock_transaction.status == "ok"

PARTIAL_LOW_YAML = """\
metadata:
  agent: frontend-sentry
  status: partial
  confidence: low
"""

def test_record_agent_run_partial():
    usage = [{"input_tokens": 500, "output_tokens": 80}]

    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        mock_transaction = MagicMock()
        mock_sentry.start_transaction.return_value.__enter__ = MagicMock(return_value=mock_transaction)
        mock_sentry.start_transaction.return_value.__exit__ = MagicMock(return_value=False)

        record_agent_run("frontend-sentry", PARTIAL_LOW_YAML, usage)

        assert mock_transaction.status == "deadline_exceeded"

def test_record_agent_run_no_dsn():
    usage = [{"input_tokens": 500, "output_tokens": 80}]

    with patch("agents.sentry_utils.sentry_sdk") as mock_sentry:
        with patch("agents.sentry_utils.AGENTS_SENTRY_DSN", ""):
            record_agent_run("frontend-sentry", COMPLETED_HIGH_YAML, usage)
            mock_sentry.init.assert_not_called()

def test_confidence_numeric_mapping():
    from agents.sentry_utils import confidence_to_numeric

    assert confidence_to_numeric("high") == 3
    assert confidence_to_numeric("medium") == 2
    assert confidence_to_numeric("low") == 1
    assert confidence_to_numeric("missing") == 0
