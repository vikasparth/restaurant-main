import os
from unittest.mock import patch, MagicMock
import requests
import pytest

from agents.sentry_api import (
    query_sentry_errors,
    get_stack_trace,
    get_affected_releases,
    _pick_issue,
    _validate_sentry_guardrails,
)

_ENV = {"SENTRY_AUTH_TOKEN": "test-token", "SENTRY_ORG_SLUG": "test-org"}

# ── _validate_sentry_guardrails ───────────────────────────────────────────────

def test_validate_guardrails_returns_none_for_valid_input():
    assert _validate_sentry_guardrails({"max_issues": 3, "max_frames": 3}) is None


def test_validate_guardrails_returns_none_for_empty_dict():
    assert _validate_sentry_guardrails({}) is None


def test_validate_guardrails_rejects_string_max_issues():
    assert _validate_sentry_guardrails({"max_issues": "three"}) is not None


def test_validate_guardrails_rejects_negative_max_frames():
    assert _validate_sentry_guardrails({"max_frames": -1}) is not None


def test_validate_guardrails_rejects_bool_as_int():
    # bool is a subclass of int in Python — must not be accepted as a valid int
    assert _validate_sentry_guardrails({"max_issues": True}) is not None


# ── query_sentry_errors ───────────────────────────────────────────────────────

def _mock_issue_response(issues: list) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = issues
    mock.raise_for_status.return_value = None
    return mock


def _raw_sentry_issue(**overrides):
    base = {
        "id": "abc123",
        "title": "TypeError: undefined",
        "level": "error",
        "culprit": "src/app.tsx",
        "count": 10,
        "userCount": 3,
        "isUnhandled": True,
        "firstSeen": "2026-05-04T09:00:00Z",
        "lastSeen": "2026-05-04T09:58:00Z",
        "firstRelease": {"version": "cfe6747"},
    }
    return {**base, **overrides}


def test_query_sentry_errors_returns_trimmed_fields():
    raw = [_raw_sentry_issue()]
    with patch("requests.get", return_value=_mock_issue_response(raw)), \
         patch.dict(os.environ, _ENV):
        result = query_sentry_errors("restaurant-frontend", "age:-1h", 3)

    assert len(result) == 1
    issue = result[0]
    assert issue["id"] == "abc123"
    assert issue["level"] == "error"
    assert issue["user_count"] == 3        # renamed from userCount
    assert issue["is_unhandled"] is True   # renamed from isUnhandled
    assert issue["release"] == "cfe6747"   # extracted from firstRelease.version
    assert "userCount" not in issue        # raw field must be dropped


def test_query_sentry_errors_passes_correct_params():
    with patch("requests.get", return_value=_mock_issue_response([])) as mock_get, \
         patch.dict(os.environ, _ENV):
        query_sentry_errors("restaurant-frontend", "age:-1h", 3)

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["query"] == "is:unresolved age:-1h"
    assert kwargs["params"]["limit"] == 3
    assert "Bearer test-token" in kwargs["headers"]["Authorization"]


def test_query_sentry_errors_propagates_401():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
    with patch("requests.get", return_value=mock_resp), \
         patch.dict(os.environ, _ENV):
        with pytest.raises(requests.exceptions.HTTPError):
            query_sentry_errors("restaurant-frontend", "age:-1h", 3)


def test_query_sentry_errors_propagates_429():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
    with patch("requests.get", return_value=mock_resp), \
         patch.dict(os.environ, _ENV):
        with pytest.raises(requests.exceptions.HTTPError):
            query_sentry_errors("restaurant-frontend", "age:-1h", 3)


def test_query_sentry_errors_propagates_timeout():
    with patch("requests.get", side_effect=requests.exceptions.Timeout), \
         patch.dict(os.environ, _ENV):
        with pytest.raises(requests.exceptions.Timeout):
            query_sentry_errors("restaurant-frontend", "age:-1h", 3)


def test_query_sentry_errors_propagates_connection_error():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError), \
         patch.dict(os.environ, _ENV):
        with pytest.raises(requests.exceptions.ConnectionError):
            query_sentry_errors("restaurant-frontend", "age:-1h", 3)


# ── get_stack_trace ───────────────────────────────────────────────────────────

def _mock_event_response(app_frames: list, non_app_frames: list = []) -> MagicMock:
    all_frames = non_app_frames + app_frames
    data = {
        "culprit": "src/app.tsx",
        "entries": [{
            "data": {
                "values": [{
                    "type": "TypeError",
                    "value": "Cannot read property 'price'",
                    "stacktrace": {"frames": all_frames},
                }]
            }
        }]
    }
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


def test_get_stack_trace_filters_to_app_frames_only():
    app_frame = {"filename": "src/app.tsx", "lineNo": 42, "function": "render", "inApp": True}
    lib_frame = {"filename": "node_modules/react/index.js", "lineNo": 1, "function": "createElement", "inApp": False}
    with patch("requests.get", return_value=_mock_event_response([app_frame], [lib_frame])), \
         patch.dict(os.environ, _ENV):
        result = get_stack_trace("abc123", max_frames=3)

    assert len(result["top_frames"]) == 1
    assert result["top_frames"][0]["filename"] == "src/app.tsx"


def test_get_stack_trace_caps_at_max_frames():
    app_frames = [
        {"filename": f"src/file{i}.tsx", "lineNo": i, "function": f"fn{i}", "inApp": True}
        for i in range(10)
    ]
    with patch("requests.get", return_value=_mock_event_response(app_frames)), \
         patch.dict(os.environ, _ENV):
        result = get_stack_trace("abc123", max_frames=2)

    assert len(result["top_frames"]) == 2


def test_get_stack_trace_returns_exception_fields():
    app_frame = {"filename": "src/app.tsx", "lineNo": 1, "function": "fn", "inApp": True}
    with patch("requests.get", return_value=_mock_event_response([app_frame])), \
         patch.dict(os.environ, _ENV):
        result = get_stack_trace("abc123", max_frames=3)

    assert result["exception_type"] == "TypeError"
    assert "price" in result["exception_message"]


# ── get_affected_releases ─────────────────────────────────────────────────────

def test_get_affected_releases_returns_version_strings():
    mock = MagicMock()
    mock.json.return_value = {"topValues": [{"value": "sha1"}, {"value": "sha2"}]}
    mock.raise_for_status.return_value = None
    with patch("requests.get", return_value=mock), \
         patch.dict(os.environ, _ENV):
        result = get_affected_releases("abc123")

    assert result == ["sha1", "sha2"]


def test_get_affected_releases_returns_empty_list_when_no_releases():
    mock = MagicMock()
    mock.json.return_value = {}   # topValues absent — project has no release tagging
    mock.raise_for_status.return_value = None
    with patch("requests.get", return_value=mock), \
         patch.dict(os.environ, _ENV):
        result = get_affected_releases("abc123")

    assert result == []


# ── _pick_issue ───────────────────────────────────────────────────────────────

def test_pick_issue_prefers_higher_severity():
    fatal = {"level": "fatal", "last_seen": "2026-05-04T08:00:00Z"}
    error = {"level": "error", "last_seen": "2026-05-04T09:00:00Z"}
    assert _pick_issue([error, fatal]) == fatal


def test_pick_issue_prefers_most_recent_when_same_level():
    older = {"level": "error", "last_seen": "2026-05-04T08:00:00Z"}
    newer = {"level": "error", "last_seen": "2026-05-04T09:58:00Z"}
    assert _pick_issue([older, newer]) == newer
