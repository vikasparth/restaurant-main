import os
import anthropic

from agents.config import (
    DIAGNOSTIC_MODEL,
    DIAGNOSTIC_MAX_TURNS,
    DIAGNOSTIC_MAX_TOKENS,
    DIAGNOSTIC_MAX_FILE_CHARS,
    STATUS_COMPLETED,
    STATUS_NO_DATA,
    STATUS_INJECTION_DETECTED,
    STATUS_INVALID_INPUT,
    STATUS_SERVER_ERROR,
    STATUS_UNAUTHENTICATED,
    STATUS_PARTIAL,
    STATUS_UNAUTHORIZED,
    STATUS_RATE_LIMITED,
    STATUS_TIMEOUT,
    STATUS_NETWORK_ERROR, 
    STATUS_SCHEMA_ERROR
)
from agents.patterns import _INJECTION_RE
from agents.sentry_utils import record_agent_run
from agents.prompt_utils import build_system_prompt

_ALLOWED_PREFIXES = ("src/", "graphql-gateway/", "backend/", "docs/")
_STUB = "[content processed]"
_SYSTEM_PROMPT = (
    "You are a codebase navigator. Read files to trace the root cause of a crash. "
    "Call return_findings when you have identified the root cause. Never return raw code."
)


def _validate_guardrails(guardrails: dict) ->str | None:
    max_files_to_read = guardrails.get("max_files_to_read")
    if not isinstance(max_files_to_read, int) or isinstance(max_files_to_read, bool):
        return "Invalid value for max_files_to_read"
    if max_files_to_read <= 0:
        return "max_files_to_read must be a positive integer"
    return None
    
def _is_path_allowed(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES)

def _read_file(path: str) -> tuple[str,bool]:
    if not _is_path_allowed(path):
        return "ERROR: path not in scope", False
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read(DIAGNOSTIC_MAX_FILE_CHARS)
    except FileNotFoundError:
        return "ERROR: file not found", False
    if _INJECTION_RE.search(content):
        return "ERROR: injection detected in file content", True
    return content, False

def _list_directory(path: str) -> list[str]:
    if not _is_path_allowed(path):
        return "ERROR: path not in scope"
    listfiles = os.listdir(path)
    return sorted(listfiles)
    
def _build_tool_definitions() -> list[dict]:
    return [
        {
            "name": "read_file",
            "description": "Read a source file from the checked-out repository.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative file path, e.g. src/hooks/useMenu.ts"}},
                "required": ["path"],
            },
        },
        {
            "name": "list_directory",
            "description": "List filenames in a directory.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative directory path"}},
                "required": ["path"],
            },
        },
        {
            "name": "return_findings",
            "description": "Submit the final structured findings. Call this when you have identified the root cause.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "crash_location":  {"type": "string"},
                    "root_cause_file": {"type": "string"},
                    "missing_field":   {"type": ["string", "null"]},
                    "fix_location":    {"type": "string"},
                    "fix_type":        {"type": "string"},
                    "fix_detail":      {"type": "string"},
                    "runbook_match":   {"type": ["string", "null"]},
                    "injection_flag":  {"type": "boolean"},
                    "pii_flag":        {"type": "boolean"},
                },
                "required": ["crash_location", "root_cause_file", "fix_location", "fix_type", "fix_detail", "injection_flag", "pii_flag"],
            },
        },
    ]

def _process_tool_call(
        tool_name: str,
        tool_input: dict,
        files_read: list[str],
        max_files: int,
) -> tuple[str,bool]:
    if tool_name == "read_file":
        if len(files_read) >= max_files:
            return "ERROR: max_files_to_read limit reached", False
        path = tool_input.get("path", "")
        content, injection = _read_file(path)
        if content.startswith("ERROR:"):
            return content, injection
        files_read.append(path)
        return content, False
    elif tool_name == "list_directory":
        path = tool_input.get("path", "")
        return str(_list_directory(path)), False
    elif tool_name == "return_findings":
        # findings are returned via tool calls, not the final response — the Orchestrator relies on this for structured output, so we don't allow any error messages here
        return "Findings captured", False
    else:
        return "ERROR: unknown tool", False
    
def _record_and_return(status: str, usage_by_turn: list, issue_number: str, extra: dict | None = None) -> dict:
    result = {"status": status, "source": "diagnostic", **(extra or {})}
    record_agent_run("diagnostic_agent", result, usage_by_turn, issue_number)
    return result


def run(guardrails: dict, issue_number: str = "") -> dict:
    usage_by_turn = []
    findings = {}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _record_and_return(STATUS_UNAUTHENTICATED, usage_by_turn, issue_number)
    error = _validate_guardrails(guardrails)
    if error:
        return _record_and_return(STATUS_INVALID_INPUT, usage_by_turn, issue_number)
    crash_location = guardrails.get("crash_location") or ""
    endpoint = guardrails.get("endpoint") or ""

    # crash_location is a precise file + line from Sentry, e.g. "src/hooks/useMenu.ts:42"
    # endpoint is a backend route from Render logs, e.g. "/api/menu" — used as fallback
    # when crash_location is None (happens until task 3.14 wires up backend Sentry SDK)
    if crash_location:
        # strip the :42 line number before checking the path prefix
        if not _is_path_allowed(crash_location.split(":")[0]):
            return _record_and_return(STATUS_NO_DATA, usage_by_turn, issue_number)
        nav_start = crash_location
    elif endpoint:
        # no scope check needed — endpoint is a URL path, not a filesystem path
        nav_start = endpoint
    else:
        return _record_and_return(STATUS_NO_DATA, usage_by_turn, issue_number)

    client = anthropic.Anthropic()
    changed_files = guardrails.get("changed_files", [])
    max_files = guardrails.get("max_files_to_read", 5)

    # cached system prompt — avoids re-sending on every turn
    system_prompt = build_system_prompt(_SYSTEM_PROMPT)

    messages = [
        {
            "role": "user",
            "content": (
                f"Navigation start: {nav_start}\n"
                f"Changed files: {changed_files}\n"
                f"Max files to read: {max_files}"
            ),
        }
    ]
    files_read: list[str] = []  # tracks paths read; enforces max_files cap in _process_tool_call
    # bounded loop — DIAGNOSTIC_MAX_TURNS prevents runaway API spend
    for _ in range(DIAGNOSTIC_MAX_TURNS):
        try:
            response = client.messages.create(
                model=DIAGNOSTIC_MODEL,
                max_tokens=DIAGNOSTIC_MAX_TOKENS,
                system=system_prompt,
                tools=_build_tool_definitions(),
                messages=messages,
            )    
        except anthropic.AuthenticationError:
            return _record_and_return(STATUS_UNAUTHENTICATED, usage_by_turn, issue_number)
        except anthropic.PermissionDeniedError:
            return _record_and_return(STATUS_UNAUTHORIZED, usage_by_turn, issue_number)
        except (anthropic.BadRequestError, anthropic.UnprocessableEntityError):
            return _record_and_return(STATUS_INVALID_INPUT, usage_by_turn, issue_number)
        except anthropic.RateLimitError:
            return _record_and_return(STATUS_RATE_LIMITED, usage_by_turn, issue_number)
        except anthropic.NotFoundError:
            return _record_and_return(STATUS_INVALID_INPUT, usage_by_turn, issue_number)
        except anthropic.APIStatusError:
            return _record_and_return(STATUS_SERVER_ERROR, usage_by_turn, issue_number)
        except anthropic.APITimeoutError:
            return _record_and_return(STATUS_TIMEOUT, usage_by_turn, issue_number)
        except anthropic.APIConnectionError:
            return _record_and_return(STATUS_NETWORK_ERROR, usage_by_turn, issue_number)

        # API is stateless — full messages list resent every turn; shrink consumed tool_results to stub before next call
        # last = messages[-1]["content"]
        # if isinstance(last, list):
        #     for entry in last:
        #         if entry.get("type") == "tool_result":
        #             entry["content"] = _STUB

        if response.stop_reason is None:
            return _record_and_return(STATUS_SCHEMA_ERROR, usage_by_turn, issue_number)
        if response.usage is None:
            return _record_and_return(STATUS_SCHEMA_ERROR, usage_by_turn, issue_number)
     
        usage_by_turn.append({"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens})

        # Claude may call multiple tools in one turn — collect all and respond to each
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        return_block = next((b for b in tool_blocks if b.name == "return_findings"), None)
        if return_block:
            # Claude finished — capture structured findings and exit loop
            findings = {**return_block.input, "status": STATUS_COMPLETED, "source": "diagnostic"}
            break

        if tool_blocks:
            tool_results = []
            for tb in tool_blocks:
                result_str, detected = _process_tool_call(
                    tb.name, tb.input, files_read, max_files
                )
                if detected:  # file content matched injection pattern — stop immediately, don't pass to Claude
                    return _record_and_return(STATUS_INJECTION_DETECTED, usage_by_turn, issue_number, {"injection_flag": True})
                tool_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": result_str})

            # append Claude's response and all tool results so the next turn has full context
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
    # loop exhausted without return_findings — return partial with whatever was found
    if not findings:
        return _record_and_return(STATUS_PARTIAL, usage_by_turn, issue_number)

    record_agent_run("diagnostic_agent", findings, usage_by_turn, issue_number)
    return findings
