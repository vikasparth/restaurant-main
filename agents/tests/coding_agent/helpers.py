"""Shared helpers for test_coding_agent_*.py test modules."""
import httpx
from unittest.mock import MagicMock


def _anthropic_status_error(exc_class, status_code):
    """Construct an Anthropic APIStatusError subclass with a mock httpx.Response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.headers = {}  # SDK accesses headers.get("request-id") on construction
    return exc_class("test error", response=mock_response, body=None)


def make_payload(
    fix_files=None,
    fix_type="null_check",
    fix_detail="Add null check before accessing user.name",
    fix_location="line 42 of src/utils/user.ts",
    confidence="high",
    injection_flag=False,
    pii_flag=False,
    diagnostic_status="completed",
):
    """Minimal valid payload matching the shape the Orchestrator assembles."""
    return {
        "diagnostic": {
            "status": diagnostic_status,
            "findings": {
                "fix_files": fix_files or ["src/utils/user.ts"],
                "fix_type": fix_type,
                "fix_detail": fix_detail,
                "fix_location": fix_location,
                "root_cause": "Null pointer on user.name when session expires",
                "affected_layer": "frontend",
                "regression": False,
                "confidence": confidence,
                "recommended_fix": "Add null guard before accessing user.name",
                "runbook_match": None,
            },
        },
        "sentry_frontend": {"status": "completed", "issues": []},
        "injection_flag": injection_flag,
        "pii_flag": pii_flag,
    }


def make_tool_use_response(
    root_cause="Null pointer on user.name when session expires",
    affected_layer="frontend",
    regression=False,
    confidence="high",
    recommended_fix="Add null guard before accessing user.name",
    runbook_match=None,
    original_snippet="const name = user.name;",
    replacement_snippet="const name = user?.name ?? 'Guest';",
):
    """Anthropic SDK response with a return_code_fix tool_use block."""
    tool_use = MagicMock()
    tool_use.type = "tool_use"
    tool_use.name = "return_code_fix"
    tool_use.input = {
        "root_cause": root_cause,
        "affected_layer": affected_layer,
        "regression": regression,
        "confidence": confidence,
        "recommended_fix": recommended_fix,
        "runbook_match": runbook_match,
        "original_snippet": original_snippet,
        "replacement_snippet": replacement_snippet,
    }
    response = MagicMock()
    response.content = [tool_use]
    response.usage = MagicMock(input_tokens=500, output_tokens=200)
    return response


def make_text_only_response():
    """Anthropic SDK response with no tool_use block — triggers schema_error."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "I cannot provide a fix."
    response = MagicMock()
    response.content = [text_block]
    response.usage = MagicMock(input_tokens=100, output_tokens=50)
    return response
