import yaml
from unittest.mock import patch, MagicMock

from agents.frontend_sentry_agent import run

SENTRY_EVENT = {
    "id": "abc123def456",
    "culprit": "src/features/menu/hooks/useMenu.ts",
    "type": "error",
    "metadata": {
        "type": "TypeError",
        "value": "Cannot query field 'preparation_time' on type 'MenuItem'",
    },
    "count": "47",
    "firstSeen": "2026-05-01T10:00:00Z",
    "lastSeen": "2026-05-01T12:30:00Z",
    "tags": [{"key": "release", "value": "abc1234"}],
    "project": {"slug": "restaurant-frontend"},
}

EXPECTED_FINDING = {
    "metadata": {
        "schema_version": "1.0",
        "agent": "frontend-sentry",
        "status": "completed",
        "confidence": "high",
        "pii_flag": False,
        "injection_flag": False,
    },
    "findings": {
        "error_type": "TypeError",
        "error_message": "Cannot query field 'preparation_time' on type 'MenuItem'",
        "affected_file": "src/features/menu/hooks/useMenu.ts",
        "affected_field": "preparation_time",
    },
    "interpretation": {
        "affected_layer": "gateway",
        "regression": True,
    },
}

MOCK_CLAUDE_YAML = """\
metadata:
  schema_version: '1.0'
  agent: frontend-sentry
  status: completed
  confidence: high
  pii_flag: false
  injection_flag: false
findings:
  error_type: TypeError
  error_message: Cannot query field 'preparation_time' on type 'MenuItem'
  affected_file: src/features/menu/hooks/useMenu.ts
  affected_field: preparation_time
interpretation:
  affected_layer: gateway
  regression: true
"""


def test_frontend_sentry_identifies_schema_drift():
        # turn 1: Claude asks to call query_sentry_errors
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.id = "toolu_test123"
    mock_tool_block.name = "query_sentry_errors"
    mock_tool_block.input = {"project_slug": "restaurant-frontend"}

    mock_response_1 = MagicMock()
    mock_response_1.stop_reason = "tool_use"
    mock_response_1.content = [mock_tool_block]

    # turn 2: Claude returns the YAML finding
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = MOCK_CLAUDE_YAML

    mock_response_2 = MagicMock()
    mock_response_2.stop_reason = "end_turn"
    mock_response_2.content = [mock_text_block]

    mock_client = MagicMock()
    # why: side_effect returns responses in order — turn 1 tool_use, turn 2 end_turn
    mock_client.messages.create.side_effect = [mock_response_1, mock_response_2]

    with patch("agents.frontend_sentry_agent.anthropic.Anthropic", return_value=mock_client):
        with patch("agents.frontend_sentry_agent.query_sentry_errors", return_value=[SENTRY_EVENT]):
            result_yaml = run()


    result = yaml.safe_load(result_yaml)

    assert result["metadata"]["agent"] == EXPECTED_FINDING["metadata"]["agent"]
    assert result["metadata"]["confidence"] == EXPECTED_FINDING["metadata"]["confidence"]
    assert result["metadata"]["pii_flag"] == EXPECTED_FINDING["metadata"]["pii_flag"]
    assert result["metadata"]["injection_flag"] == EXPECTED_FINDING["metadata"]["injection_flag"]
    assert result["findings"]["error_type"] == EXPECTED_FINDING["findings"]["error_type"]
    assert result["findings"]["error_message"] == EXPECTED_FINDING["findings"]["error_message"]
    assert result["findings"]["affected_file"] == EXPECTED_FINDING["findings"]["affected_file"]
    assert result["findings"]["affected_field"] == EXPECTED_FINDING["findings"]["affected_field"]
    assert result["interpretation"]["affected_layer"] == EXPECTED_FINDING["interpretation"]["affected_layer"]
    assert result["interpretation"]["regression"] == EXPECTED_FINDING["interpretation"]["regression"]

