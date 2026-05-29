import shutil
import subprocess
from datetime import datetime

import anthropic
import requests

from agents.config import (
    CODING_MODEL,
    CODING_MAX_TOKENS,
    GITHUB_API_BASE,
    GITHUB_REPO,
    GITHUB_TOKEN,
    GITHUB_BRANCH,
    GITHUB_PR_BRANCH_PREFIX,
    STATUS_COMPLETED,
    STATUS_NO_DATA,
    STATUS_PARTIAL,
    STATUS_INVALID_INPUT,
    STATUS_INJECTION_DETECTED,
    STATUS_UNAUTHENTICATED,
    STATUS_UNAUTHORIZED,
    STATUS_RATE_LIMITED,
    STATUS_SERVER_ERROR,
    STATUS_TIMEOUT,
    STATUS_NETWORK_ERROR,
    STATUS_SCHEMA_ERROR,
)
from agents.sentry_utils import record_agent_run, confidence_to_numeric
from agents.prompt_utils import build_system_prompt

_SYSTEM_PROMPT = (
    "You are a precise code editor. You will receive a file's full content and a "
    "diagnosis of what is wrong. Generate an exact original_snippet (lines to replace, "
    "must exist verbatim in the file) and a replacement_snippet (the corrected code). "
    "Do not refactor surrounding code. Do not touch any lines outside the identified location."
)

_VALID_CONFIDENCE = {"high", "medium", "low"}
_VALID_LAYERS = {"frontend", "backend", "graphql", "database", "unknown"}


def _validate_payload(payload: dict) -> str | None:
    if not isinstance(payload, dict) or not payload:
        return "Payload must be a JSON object."

    if "diagnostic" not in payload:
        return "Missing 'diagnostic' key in input."
    if payload["diagnostic"]["status"] == STATUS_NO_DATA:
        return STATUS_NO_DATA
    if payload["diagnostic"]["status"] not in (STATUS_COMPLETED, STATUS_PARTIAL):
        return "Diagnostic status must be 'completed' or 'partial'."
    findings = payload["diagnostic"].get("findings") or {}
    for field in ("fix_files", "fix_type", "fix_detail"):
        if field not in findings:
            return f"Diagnostic findings missing required field: '{field}'."
    return None


def _should_open_pr(confidence: str) -> bool:
    if confidence in ("high", "medium"):
        return True
    return False


def _apply_patch(
    file_content: str, original_snippet: str, replacement_snippet: str
) -> str | None:
    if not original_snippet.strip():
        return None
    if file_content.count(original_snippet) != 1:
        return None
    return file_content.replace(original_snippet, replacement_snippet)


def _parse_code_fix(response) -> dict | None:
    for part in response.content:
        if (
            getattr(part, "type", "") == "tool_use"
            and getattr(part, "name", "") == "return_code_fix"
        ):
            return part.input
    return None


def _validate_fix(fix: dict) -> str | None:
    if "original_snippet" not in fix:
        return "Tool use block missing 'original_snippet'."
    if fix.get("confidence") not in _VALID_CONFIDENCE:
        return f"Invalid confidence level: {fix.get('confidence')}. Must be one of {_VALID_CONFIDENCE}."
    if not isinstance(fix.get("regression"), bool):
        return "Regression field must be a boolean."
    return None


def _check_environment() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
    )
    if result.returncode != 0:
        return "Current directory is not a Git repository."
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != "":
        return "Git repository has uncommitted changes. Please commit or stash them before running the Coding Agent."
    if shutil.which("pre-commit") is None:
        return "pre-commit not found in PATH. Please install pre-commit and ensure it's available in the command line."
    if not GITHUB_TOKEN:
        return "GitHub token not found in environment variables."
    return None


def _read_local_file(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def _build_tool_definitions() -> list[dict]:
    return [
        {
            "name": "return_code_fix",
            "description": "Return the root cause analysis and exact code fix.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "root_cause": {"type": "string"},
                    "affected_layer": {"type": "string", "enum": list(_VALID_LAYERS)},
                    "regression": {"type": "boolean"},
                    "confidence": {"type": "string", "enum": list(_VALID_CONFIDENCE)},
                    "recommended_fix": {"type": "string"},
                    "runbook_match": {"type": ["string", "null"]},
                    "original_snippet": {"type": "string"},
                    "replacement_snippet": {"type": "string"},
                },
                "required": [
                    "root_cause",
                    "affected_layer",
                    "regression",
                    "confidence",
                    "recommended_fix",
                    "original_snippet",
                    "replacement_snippet",
                ],
            },
        }
    ]


def _commit_and_push(
    file_path: str, patched_content: str, branch_name: str, commit_message: str
) -> tuple[str | None, str | None]:
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name], capture_output=True, text=True
    )
    if result.returncode != 0:
        return None, "push_failed"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(patched_content)
    result = subprocess.run(["git", "add", file_path], capture_output=True, text=True)
    if result.returncode != 0:
        subprocess.run(
            ["git", "checkout", GITHUB_BRANCH], capture_output=True, text=True
        )
        subprocess.run(
            ["git", "branch", "-d", branch_name], capture_output=True, text=True
        )
        return None, "push_failed"
    result = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
    if result.returncode != 0:
        subprocess.run(
            ["git", "checkout", GITHUB_BRANCH], capture_output=True, text=True
        )
        subprocess.run(
            ["git", "branch", "-d", branch_name], capture_output=True, text=True
        )
        return None, "test_regression"
    result = subprocess.run(
        ["git", "commit", "-m", commit_message], capture_output=True, text=True
    )
    if result.returncode != 0:
        subprocess.run(
            ["git", "checkout", GITHUB_BRANCH], capture_output=True, text=True
        )
        subprocess.run(
            ["git", "branch", "-d", branch_name], capture_output=True, text=True
        )
        return None, "hook_failure"
    result = subprocess.run(
        ["git", "push", "origin", branch_name], capture_output=True, text=True
    )
    if result.returncode != 0:
        subprocess.run(
            ["git", "checkout", GITHUB_BRANCH], capture_output=True, text=True
        )
        subprocess.run(
            ["git", "branch", "-d", branch_name], capture_output=True, text=True
        )
        return None, "push_failed"
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    )
    sha = result.stdout.strip()
    return sha, None


def _format_pr_body(
    interpretation: dict,
    payload: dict,
    file_changed: str,
    remaining_files: list[str],
    issue_number: str,
) -> str:
    lines = [
        "## Root Cause",
        interpretation.get("root_cause", ""),
        "",
        f"**Affected layer:** {interpretation.get('affected_layer', 'unknown')}",
        f"**Confidence:** {interpretation.get('confidence', 'unknown')}",
        f"**Regression:** {interpretation.get('regression', False)}",
        "",
        "## Recommended Fix",
        interpretation.get("recommended_fix", ""),
        "",
        "## Files Changed",
        f"- `{file_changed}` (auto-committed)",
    ]
    if remaining_files:
        lines.append("")
        lines.append("## Also Requires Manual Changes")
        for f in remaining_files:
            lines.append(f"- `{f}`")
    sources = [
        k
        for k in ("sentry_frontend", "sentry_backend", "render_logs", "github")
        if k in payload
    ]
    if sources:
        lines += ["", "## Evidence Sources", ", ".join(sources)]
    if issue_number:
        lines += ["", f"Closes #{issue_number}"]
    lines += [
        "",
        "---",
        "🤖 Opened automatically by the Coding Agent. **Draft — do not merge without review.**",
    ]
    return "\n".join(lines)


def _open_draft_pr(
    branch_name: str,
    interpretation: dict,
    payload: dict,
    file_changed: str,
    remaining_files: list[str],
    issue_number: str,
) -> str | None:
    pr_title = f"Fix: {interpretation.get('recommended_fix', 'automated fix')[:60]}"
    pr_body = _format_pr_body(
        interpretation, payload, file_changed, remaining_files, issue_number
    )
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/pulls"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    data = {
        "title": pr_title,
        "head": branch_name,
        "base": GITHUB_BRANCH,
        "body": pr_body,
        "draft": True,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.ok:
            return response.json()["html_url"]
    except Exception:
        pass
    return None


def run(payload: dict, issue_number: str = "") -> dict:
    usage_by_turn: list[dict] = []

    def _return(result: dict) -> dict:
        record_agent_run("coding_agent", result, usage_by_turn, issue_number)
        return result

    # ── injection guard ───────────────────────────────────────────────────────
    if isinstance(payload, dict) and payload.get("injection_flag"):
        return _return({"status": STATUS_INJECTION_DETECTED, "source": "coding"})

    # ── payload validation ────────────────────────────────────────────────────
    validation_error = _validate_payload(payload)
    if validation_error == STATUS_NO_DATA:
        return _return({"status": STATUS_NO_DATA, "source": "coding"})
    if validation_error:
        return _return(
            {
                "status": STATUS_INVALID_INPUT,
                "source": "coding",
                "error": validation_error,
            }
        )

    # ── environment check ─────────────────────────────────────────────────────
    env_error = _check_environment()
    if env_error:
        return _return(
            {"status": STATUS_INVALID_INPUT, "source": "coding", "error": env_error}
        )

    findings = payload["diagnostic"]["findings"]
    fix_files = findings["fix_files"]
    fix_location = findings.get("fix_location", "")
    fix_type = findings["fix_type"]
    fix_detail = findings["fix_detail"]
    file_content = _read_local_file(fix_files[0])

    # ── Claude call ───────────────────────────────────────────────────────────
    user_message = (
        f"File: {fix_files[0]}\n\n"
        f"Fix type: {fix_type}\n"
        f"Fix detail: {fix_detail}\n"
        f"Fix location: {fix_location}\n\n"
        f"File content:\n```\n{file_content}\n```"
    )
    client = anthropic.Anthropic()
    # cached system prompt — avoids re-sending on every turn
    system_prompt = build_system_prompt(_SYSTEM_PROMPT)
    try:
        response = client.messages.create(
            model=CODING_MODEL,
            max_tokens=CODING_MAX_TOKENS,
            system=system_prompt,
            tools=_build_tool_definitions(),
            messages=[{"role": "user", "content": user_message}],
            tool_choice={"type": "any"},
        )
        usage_by_turn.append(
            {
                "model": CODING_MODEL,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )
        fix = _parse_code_fix(response)
        if fix is None:
            return _return({"status": STATUS_SCHEMA_ERROR, "source": "coding"})
        validation_error = _validate_fix(fix)
        if validation_error is not None:
            return _return({"status": STATUS_SCHEMA_ERROR, "source": "coding"})

    except anthropic.APIStatusError as e:
        code = e.status_code
        if code == 401:
            status = STATUS_UNAUTHENTICATED
        elif code == 403:
            status = STATUS_UNAUTHORIZED
        elif code in (400, 404, 422):
            status = STATUS_INVALID_INPUT
        elif code == 429:
            status = STATUS_RATE_LIMITED
        elif code >= 500:
            status = STATUS_SERVER_ERROR
        else:
            status = STATUS_SERVER_ERROR
        return _return(
            {
                "status": status,
                "source": "coding",
                "error": f"Claude API error with status code {code}.",
            }
        )
    except anthropic.APITimeoutError:
        return _return(
            {
                "status": STATUS_TIMEOUT,
                "source": "coding",
                "error": "Request to Claude API timed out.",
            }
        )
    except anthropic.APIConnectionError:
        return _return(
            {
                "status": STATUS_NETWORK_ERROR,
                "source": "coding",
                "error": "Network error while connecting to Claude API.",
            }
        )

    # ── commit + PR flow ──────────────────────────────────────────────────────
    branch_name = f"{GITHUB_PR_BRANCH_PREFIX}{issue_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    commit_message = f"fix: {fix_type} in {fix_files[0]}"
    _apply_patch_result = _apply_patch(
        file_content, fix["original_snippet"], fix["replacement_snippet"]
    )
    if _apply_patch_result is None:
        return _return(
            {
                "status": STATUS_PARTIAL,
                "source": "coding",
                "interpretation": {
                    "root_cause": fix["root_cause"],
                    "affected_layer": fix["affected_layer"],
                    "regression": fix["regression"],
                    "confidence": fix["confidence"],
                    "recommended_fix": fix["recommended_fix"],
                    "runbook_match": fix["runbook_match"],
                },
                "file_changed": None,
                "remaining_files": fix_files[1:],
                "commit_sha": None,
                "pr_url": None,
                "partial_code": "hallucination_guard",
                "partial_reason": "Original snippet not found in file, or original snippet is empty. No changes have been made to the codebase due to this uncertainty.",
                # fix_files[0] also needs manual attention here — Orchestrator must check file_changed=None to catch it
                "pii_flag": payload.get("pii_flag", False),
                "injection_flag": payload.get("injection_flag", False),
            }
        )
    interpretation = {
        "root_cause": fix["root_cause"],
        "affected_layer": fix["affected_layer"],
        "regression": fix["regression"],
        "confidence": fix["confidence"],
        "confidence_numeric": confidence_to_numeric(fix["confidence"]),
        "recommended_fix": fix["recommended_fix"],
        "runbook_match": fix["runbook_match"],
    }
    if not _should_open_pr(fix["confidence"]):
        return _return(
            {
                "status": STATUS_COMPLETED,
                "source": "coding",
                "interpretation": interpretation,
                "file_changed": None,
                "remaining_files": fix_files[1:],
                "commit_sha": None,
                "pr_url": None,
                "pii_flag": payload.get("pii_flag", False),
                "injection_flag": payload.get("injection_flag", False),
            }
        )
    else:
        commit_sha, partial_code = _commit_and_push(
            fix_files[0], _apply_patch_result, branch_name, commit_message
        )
        if partial_code is not None:
            return _return(
                {
                    "status": STATUS_PARTIAL,
                    "source": "coding",
                    "interpretation": interpretation,
                    "file_changed": fix_files[0],
                    "remaining_files": fix_files[1:],
                    "commit_sha": None,
                    "pr_url": None,
                    "partial_code": partial_code,
                    "partial_reason": "Failed to commit and push code changes. No PR has been opened due to this failure.",
                    "pii_flag": payload.get("pii_flag", False),
                    "injection_flag": payload.get("injection_flag", False),
                }
            )
        if commit_sha is not None:
            pr_url = _open_draft_pr(
                branch_name,
                interpretation,
                payload,
                fix_files[0],
                fix_files[1:],
                issue_number,
            )
            if pr_url is None:
                return _return(
                    {
                        "status": STATUS_PARTIAL,
                        "source": "coding",
                        "interpretation": interpretation,
                        "file_changed": fix_files[0],
                        "remaining_files": fix_files[1:],
                        "commit_sha": commit_sha,
                        "pr_url": None,
                        "partial_code": "pr_failed",
                        "partial_reason": f"Code changes have been committed and pushed to a new branch, but failed to create a PR. Please check the repository for branch {branch_name} and review the changes manually.",
                        "pii_flag": payload.get("pii_flag", False),
                        "injection_flag": payload.get("injection_flag", False),
                    }
                )
            else:
                return _return(
                    {
                        "status": STATUS_COMPLETED,
                        "source": "coding",
                        "interpretation": interpretation,
                        "file_changed": fix_files[0],
                        "remaining_files": fix_files[1:],
                        "commit_sha": commit_sha,
                        "pr_url": pr_url,
                        "partial_code": None,
                        "partial_reason": None,
                        "pii_flag": payload.get("pii_flag", False),
                        "injection_flag": payload.get("injection_flag", False),
                    }
                )
