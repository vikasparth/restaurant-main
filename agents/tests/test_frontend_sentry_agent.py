import yaml
from unittest.mock import patch

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

def test_frontend_sentry_identifies_schema_drift():
    with patch("agents.frontend_sentry_agent.query_sentry_errors", return_value=[SENTRY_EVENT]):
        from agents.frontend_sentry_agent import run
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

