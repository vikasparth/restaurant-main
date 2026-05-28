"""Tests 1–16 + 42: happy path, input validation, hallucination guard."""
from unittest.mock import patch, MagicMock
import re

import agents.coding_agent as coding_agent
from agents.config import (
    STATUS_COMPLETED,
    STATUS_PARTIAL,
    STATUS_NO_DATA,
    STATUS_INVALID_INPUT,
    STATUS_INJECTION_DETECTED,
    GITHUB_PR_BRANCH_PREFIX,
)
from agents.tests.coding_agent.helpers import make_payload, make_tool_use_response


# ── Category 1: Happy Path ────────────────────────────────────────────────────

def test_high_confidence_returns_completed_with_pr_and_commit():
    payload = make_payload(confidence="high")
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(confidence="high")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_COMPLETED
    assert result["commit_sha"] == "abc123"
    assert result["pr_url"] == "https://github.com/org/repo/pull/1"
    assert result["file_changed"] == "src/utils/user.ts"
    assert result["remaining_files"] == []


def test_medium_confidence_returns_completed_with_pr_and_commit():
    payload = make_payload(confidence="medium")
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(confidence="medium")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_COMPLETED
    assert result["commit_sha"] == "abc123"
    assert result["pr_url"] == "https://github.com/org/repo/pull/1"


def test_low_confidence_returns_completed_without_pr_or_commit():
    payload = make_payload(confidence="low")
    mock_commit = MagicMock()
    mock_pr = MagicMock()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", mock_commit),
        patch.object(coding_agent, "_open_draft_pr", mock_pr),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(confidence="low")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_COMPLETED
    assert result["pr_url"] is None
    assert result["commit_sha"] is None
    mock_commit.assert_not_called()
    mock_pr.assert_not_called()


def test_multi_file_fix_commits_only_primary_file():
    payload = make_payload(fix_files=["src/utils/user.ts", "src/components/Profile.tsx"])
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)) as mock_commit,
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["file_changed"] == "src/utils/user.ts"
    assert result["remaining_files"] == ["src/components/Profile.tsx"]
    committed_path = mock_commit.call_args[0][0]
    assert committed_path == "src/utils/user.ts"


def test_pr_branch_name_includes_issue_number_and_timestamp():
    payload = make_payload()
    mock_commit = MagicMock(return_value=("abc123", None))
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", mock_commit),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        coding_agent.run(payload, issue_number="42")

    branch_name = mock_commit.call_args[0][2]
    pattern = rf"^{re.escape(GITHUB_PR_BRANCH_PREFIX)}42-\d{{14}}$"
    assert re.match(pattern, branch_name), f"Branch name '{branch_name}' does not match pattern"


def test_file_content_passed_to_claude_in_user_message():
    payload = make_payload()
    file_content = "const name = user.name;"
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value=file_content),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        coding_agent.run(payload, issue_number="42")

    create_kwargs = mock_cls.return_value.messages.create.call_args
    messages = create_kwargs[1].get("messages") or create_kwargs[0][0]
    user_message = next(m for m in messages if m["role"] == "user")
    assert file_content in user_message["content"]


# ── Category 2: Input Validation ─────────────────────────────────────────────

def test_none_payload_returns_invalid_input_without_any_call():
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push") as mock_commit,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(None, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()
    mock_commit.assert_not_called()


def test_empty_dict_payload_returns_invalid_input():
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run({}, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()


def test_missing_diagnostic_key_returns_invalid_input():
    payload = {"sentry_frontend": {}, "injection_flag": False, "pii_flag": False}
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()


def test_diagnostic_status_no_data_returns_no_data():
    payload = make_payload(diagnostic_status="no_data")
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_NO_DATA
    mock_cls.return_value.messages.create.assert_not_called()


def test_injection_flag_true_returns_injection_detected():
    payload = make_payload(injection_flag=True)
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push") as mock_commit,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INJECTION_DETECTED
    mock_cls.return_value.messages.create.assert_not_called()
    mock_commit.assert_not_called()


def test_non_dict_payload_returns_invalid_input():
    with (
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run("not a dict", issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()


def test_invalid_environment_returns_invalid_input():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value="pre-commit not installed"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "record_agent_run"),
    ):
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_INVALID_INPUT
    mock_cls.return_value.messages.create.assert_not_called()


# ── Category 3: Hallucination Guard ──────────────────────────────────────────

def test_snippet_not_found_in_file_returns_partial_with_interpretation():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="completely different content"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_apply_patch", return_value=None),
        patch.object(coding_agent, "_commit_and_push") as mock_commit,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "hallucination_guard"
    assert result["partial_reason"] is not None
    assert result["interpretation"] is not None
    assert result["commit_sha"] is None
    mock_commit.assert_not_called()


def test_empty_original_snippet_returns_partial():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push") as mock_commit,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response(original_snippet="")
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "hallucination_guard"
    mock_commit.assert_not_called()


def test_pre_commit_hook_failure_returns_partial_with_interpretation():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=(None, "hook_failure")),
        patch.object(coding_agent, "_open_draft_pr") as mock_pr,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "hook_failure"
    assert result["partial_reason"] is not None
    assert result["interpretation"] is not None
    assert result["pr_url"] is None
    mock_pr.assert_not_called()


def test_pytest_failure_returns_partial_with_interpretation():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=(None, "test_regression")),
        patch.object(coding_agent, "_open_draft_pr") as mock_pr,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "test_regression"
    assert result["partial_reason"] is not None
    assert result["interpretation"] is not None
    assert result["commit_sha"] is None
    mock_pr.assert_not_called()
