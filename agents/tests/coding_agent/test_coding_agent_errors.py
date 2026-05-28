"""Tests 17–36: authentication, authorization, not found, rate limit, server/network errors, schema."""
from unittest.mock import patch, MagicMock
import requests as requests_lib
from anthropic import (
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    RateLimitError,
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
    BadRequestError,
    ConflictError,
    UnprocessableEntityError,
)

import agents.coding_agent as coding_agent
from agents.config import (
    STATUS_PARTIAL,
    STATUS_INVALID_INPUT,
    STATUS_UNAUTHENTICATED,
    STATUS_UNAUTHORIZED,
    STATUS_RATE_LIMITED,
    STATUS_SERVER_ERROR,
    STATUS_TIMEOUT,
    STATUS_NETWORK_ERROR,
    STATUS_SCHEMA_ERROR,
)
from agents.tests.coding_agent.helpers import (
    make_payload,
    make_tool_use_response,
    make_text_only_response,
    _anthropic_status_error,
)


def _with_env_and_file(mock_cls_path="agents.coding_agent.anthropic.Anthropic"):
    """Return a tuple of standard patches needed before the Claude call."""
    return (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
    )


# ── Category 4: Authentication ────────────────────────────────────────────────

def test_anthropic_authentication_error_returns_unauthenticated():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(AuthenticationError, 401)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_UNAUTHENTICATED


def test_github_token_empty_detected_by_environment_check():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value="GITHUB_TOKEN is not set"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()


def test_git_push_auth_failure_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=(None, "push_failed")),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "push_failed"
    assert result["interpretation"] is not None


# ── Category 5: Authorization ─────────────────────────────────────────────────

def test_anthropic_permission_denied_returns_unauthorized():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(PermissionDeniedError, 403)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_UNAUTHORIZED


def test_github_403_on_pr_creation_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value=None),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "pr_failed"
    assert result["commit_sha"] == "abc123"
    assert result["pr_url"] is None


# ── Category 6: Not Found ─────────────────────────────────────────────────────

def test_anthropic_model_not_found_returns_invalid_input():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(NotFoundError, 404)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT


# ── Category 7: Rate Limiting ─────────────────────────────────────────────────

def test_anthropic_rate_limit_returns_rate_limited_without_retry():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(RateLimitError, 429)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_RATE_LIMITED
    mock_cls.return_value.messages.create.assert_called_once()


# ── Category 8: Server Failures ───────────────────────────────────────────────

def test_anthropic_server_error_returns_server_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(APIStatusError, 500)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SERVER_ERROR


def test_anthropic_timeout_returns_timeout():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = APITimeoutError(request=MagicMock())
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_TIMEOUT


def test_git_push_failure_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=(None, "push_failed")),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "push_failed"


def test_github_500_on_pr_creation_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value=None),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "pr_failed"
    assert result["commit_sha"] == "abc123"
    assert result["pr_url"] is None


# ── Category 9: Network Failures ──────────────────────────────────────────────

def test_anthropic_connection_error_returns_network_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = APIConnectionError(request=MagicMock())
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_NETWORK_ERROR


def test_github_connection_error_on_pr_creation_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value=None),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "pr_failed"


# ── Category 10 (Anthropic 4xx) ───────────────────────────────────────────────

def test_anthropic_bad_request_returns_invalid_input():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(BadRequestError, 400)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT


def test_anthropic_conflict_returns_server_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(ConflictError, 409)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SERVER_ERROR


def test_anthropic_unprocessable_entity_returns_invalid_input():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.side_effect = _anthropic_status_error(UnprocessableEntityError, 422)
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT


# ── Category 11: Schema Validation ────────────────────────────────────────────

def test_claude_response_with_no_tool_use_returns_schema_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_text_only_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SCHEMA_ERROR


def test_missing_original_snippet_field_returns_schema_error():
    payload = make_payload()
    response = make_tool_use_response()
    del response.content[0].input["original_snippet"]
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = response
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SCHEMA_ERROR


def test_invalid_confidence_value_returns_schema_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(confidence="very_high")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SCHEMA_ERROR


def test_regression_wrong_type_returns_schema_error():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(regression="true")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_SCHEMA_ERROR
