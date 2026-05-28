"""Tests 37–41: observability — usage_by_turn, record_agent_run call contract, call ordering, cleanup."""
from unittest.mock import patch, MagicMock, call
import subprocess

import agents.coding_agent as coding_agent
from agents.config import STATUS_COMPLETED, STATUS_INVALID_INPUT, STATUS_PARTIAL, GITHUB_BRANCH
from agents.tests.coding_agent.helpers import make_payload, make_tool_use_response


def test_usage_by_turn_has_exactly_one_entry():
    payload = make_payload()
    captured = {}

    def capture_record(agent_name, result, usage_by_turn, issue_number=""):
        captured["usage_by_turn"] = usage_by_turn

    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run", side_effect=capture_record),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        coding_agent.run(payload, issue_number="42")

    assert len(captured["usage_by_turn"]) == 1


def test_record_agent_run_called_on_completed_path():
    payload = make_payload()
    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", return_value=("abc123", None)),
        patch.object(coding_agent, "_open_draft_pr", return_value="https://github.com/org/repo/pull/1"),
        patch.object(coding_agent, "record_agent_run") as mock_record,
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    mock_record.assert_called_once()
    args = mock_record.call_args[0]
    assert args[0] == "coding_agent"
    assert args[1]["status"] == STATUS_COMPLETED
    assert isinstance(args[2], list)
    assert args[3] == "42"


def test_record_agent_run_called_on_invalid_input_path():
    with (
        patch.object(coding_agent, "record_agent_run") as mock_record,
    ):
        coding_agent.run(None, issue_number="42")

    mock_record.assert_called_once()
    args = mock_record.call_args[0]
    assert args[1]["status"] == STATUS_INVALID_INPUT


def test_git_commit_called_before_pr_opened():
    payload = make_payload()
    call_order = []

    def mock_commit(*args, **kwargs):
        call_order.append("commit")
        return ("abc123", None)

    def mock_pr(*args, **kwargs):
        call_order.append("pr")
        return "https://github.com/org/repo/pull/1"

    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch.object(coding_agent, "_commit_and_push", side_effect=mock_commit),
        patch.object(coding_agent, "_open_draft_pr", side_effect=mock_pr),
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        coding_agent.run(payload, issue_number="42")

    assert call_order == ["commit", "pr"]


def test_working_tree_clean_after_hook_failure():
    """Verify _commit_and_push issues cleanup git calls when pre-commit hook fails."""
    payload = make_payload()
    branch_name_used = []

    def mock_subprocess_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        # capture the branch name from the checkout -b call
        if cmd[:3] == ["git", "checkout", "-b"]:
            branch_name_used.append(cmd[3])
        # simulate hook failure on git commit
        if cmd[:2] == ["git", "commit"]:
            result.returncode = 1
            result.stderr = "pre-commit hook failed"
        return result

    with (
        patch.object(coding_agent, "_check_environment", return_value=None),
        patch.object(coding_agent, "_read_local_file", return_value="const name = user.name;"),
        patch("agents.coding_agent.anthropic.Anthropic") as mock_cls,
        patch("agents.coding_agent.subprocess.run", side_effect=mock_subprocess_run) as mock_sub,
        patch("builtins.open", MagicMock()),
        patch.object(coding_agent, "_open_draft_pr") as mock_pr,
        patch.object(coding_agent, "record_agent_run"),
    ):
        mock_cls.return_value.messages.create.return_value = make_tool_use_response()
        result = coding_agent.run(payload, issue_number="42")

    assert result["status"] == STATUS_PARTIAL
    assert result["partial_code"] == "hook_failure"
    mock_pr.assert_not_called()

    # verify cleanup: checkout back to base branch and delete the failed branch
    all_cmds = [c[0][0] for c in mock_sub.call_args_list]
    assert ["git", "checkout", GITHUB_BRANCH] in all_cmds
    if branch_name_used:
        assert ["git", "branch", "-d", branch_name_used[0]] in all_cmds
