import re
import requests

from agents.config import (
    GITHUB_API_BASE,
    GITHUB_REPO,
    GITHUB_TOKEN,
    GITHUB_BRANCH,
    GITHUB_MAX_COMMITS,
    GITHUB_MSG_MAX_LEN,
    GITHUB_MAX_FILES_PER_COMMIT,
    STATUS_COMPLETED,
    STATUS_NO_DATA,
    STATUS_INJECTION_DETECTED,
    STATUS_INVALID_INPUT,
    STATUS_UNAUTHENTICATED,
    STATUS_UNAUTHORIZED,
    STATUS_NOT_FOUND,
    STATUS_RATE_LIMITED,
    STATUS_SERVER_ERROR,
    STATUS_TIMEOUT,
    STATUS_NETWORK_ERROR,
    STATUS_SCHEMA_ERROR,
)
from agents.patterns import _INJECTION_RE, _EMAIL_RE, _PHONE_RE
from agents.sentry_utils import record_agent_run

_VALID_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")

GITHUB_PLATFORM_MAX_COMMITS = 100  # GitHub silently caps per_page at 100


def _record_and_return(status: str, usage_by_turn: list, issue_number: str, extra: dict | None = None) -> dict:
    result = {"status": status, "source": "github", **(extra or {})}
    record_agent_run("github_extractor", result, usage_by_turn, issue_number)
    return result

def _validate_guardrails(guardrails: dict) -> str | None:
    # returns an error message string if invalid, None if valid
    max_commits = guardrails.get("max_commits", GITHUB_MAX_COMMITS)
    if not isinstance(max_commits, int) or isinstance(max_commits, bool):
        return "Invalid 'max_commits' value. Expected an integer."
    if max_commits <= 0:
        return "Invalid 'max_commits' value. Expected a positive integer."
    if max_commits > GITHUB_PLATFORM_MAX_COMMITS:
        return f"Invalid 'max_commits' value. Maximum allowed is {GITHUB_PLATFORM_MAX_COMMITS}."
    
    max_files_per_commit = guardrails.get("max_files_per_commit", GITHUB_MAX_FILES_PER_COMMIT)
    if not isinstance(max_files_per_commit, int) or isinstance(max_files_per_commit, bool):
        return "Invalid 'max_files_per_commit' value. Expected an integer." 
    if max_files_per_commit < 0:
        return "Invalid 'max_files_per_commit' value. Expected a positive integer."

    release_sha = guardrails.get("release_sha")    
    if release_sha is not None:
        if not isinstance(release_sha, str):
            return "Invalid 'release_sha' value. Expected a string."
        if not _VALID_SHA_RE.match(release_sha):
            return "Invalid 'release_sha' format. Expected a valid Git SHA."
    return None

def _fetch_commits(anchor_sha: str, max_commits: int) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/commits"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, params={"sha": anchor_sha, "per_page": max_commits})
    response.raise_for_status()
    return response.json()

def _fetch_changed_files(sha: str, max_files: int) -> list[str]:
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/commits/{sha}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return [f["filename"] for f in response.json().get("files", [])][:max_files]

def _trim_commit(raw: dict) -> dict:
    sha = raw["sha"]
    author = raw["author"]["login"]  # GitHub login only — commit.author.email is never read (PII)
    committed_at = raw["commit"]["author"]["date"]
    message = raw["commit"]["message"]
    if _INJECTION_RE.search(message):
        return {"sha": sha, "injection_flag": True, "pii_flag": False}
    pii_flag = bool(_EMAIL_RE.search(message) or _PHONE_RE.search(message))
    message = message.splitlines()[0][:GITHUB_MSG_MAX_LEN]
    return {
        "sha": sha,
        "message": message,
        "author": author,
        "committed_at": committed_at,
        "injection_flag": False,
        "pii_flag": pii_flag,
    }

def run(guardrails: dict, issue_number: str = "") -> dict:
    # validates guardrails → checks token → fetches commits → validates schema → trims and flags → returns structured findings
    usage_by_turn = []  # pure Python extractor — no Claude calls, list stays empty
    error = _validate_guardrails(guardrails)
    if error:
        return _record_and_return(STATUS_INVALID_INPUT, usage_by_turn, issue_number)
    if not GITHUB_TOKEN:
        return _record_and_return(STATUS_UNAUTHENTICATED, usage_by_turn, issue_number)

    max_commits = guardrails.get("max_commits", GITHUB_MAX_COMMITS)
    max_files = guardrails.get("max_files_per_commit", GITHUB_MAX_FILES_PER_COMMIT)
    release_sha = guardrails.get("release_sha", "")
    anchor = release_sha if release_sha else GITHUB_BRANCH  # walk back from release SHA, or HEAD
    try:
        raw_commits = _fetch_commits(anchor, max_commits)
    except requests.exceptions.Timeout:
        return _record_and_return(STATUS_TIMEOUT, usage_by_turn, issue_number)
    except requests.exceptions.ConnectionError:
        return _record_and_return(STATUS_NETWORK_ERROR, usage_by_turn, issue_number)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        # dict lookup maps HTTP status codes to our constants; unlisted codes (e.g. 500) fall back to server_error
        status = {401: STATUS_UNAUTHENTICATED, 403: STATUS_UNAUTHORIZED, 404: STATUS_NOT_FOUND, 429: STATUS_RATE_LIMITED}.get(code, STATUS_SERVER_ERROR)
        return _record_and_return(status, usage_by_turn, issue_number)

    if not raw_commits:
        return _record_and_return(STATUS_NO_DATA, usage_by_turn, issue_number, {"commit_count": 0})

    # validate before processing — a missing field mid-loop would give a confusing KeyError
    for commit in raw_commits:
        try:
            _ = commit["sha"]
            _ = commit["commit"]["message"]
            _ = commit["commit"]["author"]["date"]
            _ = commit["author"]["login"]
        except (KeyError, TypeError):
            return _record_and_return(STATUS_SCHEMA_ERROR, usage_by_turn, issue_number)

    commits = []
    pii_flag = False
    for raw in raw_commits:
        trimmed = _trim_commit(raw)
        # injection in any single commit poisons the whole run — stop immediately
        if trimmed.get("injection_flag"):
            return _record_and_return(STATUS_INJECTION_DETECTED, usage_by_turn, issue_number, {"injection_flag": True})
        pii_flag = pii_flag or trimmed.pop("pii_flag", False)  # accumulate across all commits
        trimmed.pop("injection_flag", None)  # remove internal flag before adding to output
        trimmed["changed_files"] = _fetch_changed_files(trimmed["sha"], max_files)[:max_files]
        commits.append(trimmed)

    result = {
        "status": STATUS_COMPLETED,
        "source": "github",
        "commit_window": {
            "branch": GITHUB_BRANCH,
            "from_sha": raw_commits[-1]["sha"],  # oldest — GitHub returns newest first
            "to_sha": raw_commits[0]["sha"],      # newest = the anchor (release SHA or HEAD)
        },
        "commit_count": len(commits),
        "commits": commits,
        "injection_flag": False,
        "pii_flag": pii_flag,
    }
    record_agent_run("github_extractor", result, usage_by_turn, issue_number)
    return result
