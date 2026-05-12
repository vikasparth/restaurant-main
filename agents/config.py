from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# why: load agents/.env before reading any os.getenv() calls below —
# override=False means vars already set in the shell (CI, Render) take precedence
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

_SONNET = "claude-sonnet-4-6"

# why: only two components call Claude — Recommendation Agent (cross-source synthesis)
# and Orchestrator (routing + authorization). All extractors are pure Python.
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", _SONNET)
RECOMMENDATION_MODEL = os.getenv("RECOMMENDATION_MODEL", _SONNET)
# why: Codebase Extractor uses Claude for navigation (multi-hop code tracing)
# but not interpretation — still needs a model, just a different role
CODEBASE_MODEL = os.getenv("CODEBASE_MODEL", _SONNET)

SENTRY_API_BASE = os.getenv("SENTRY_API_BASE", "https://sentry.io/api/0")
AGENTS_SENTRY_DSN = os.getenv("AGENTS_SENTRY_DSN", "")

# why: shared turn/token budgets for the two Claude-calling components
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "5"))
AGENT_MAX_TOKENS_PER_TURN = int(os.getenv("AGENT_MAX_TOKENS_PER_TURN", "1024"))

CODEBASE_MAX_TURNS = int(os.getenv("CODEBASE_MAX_TURNS", "8"))
CODEBASE_MAX_TOKENS = int(os.getenv("CODEBASE_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

RECOMMENDATION_MAX_TURNS = int(os.getenv("RECOMMENDATION_MAX_TURNS", "1"))
RECOMMENDATION_MAX_TOKENS = int(os.getenv("RECOMMENDATION_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

# why: ladder starts at shortest window — extractor escalates only when zero issues found.
# parsed as comma-separated string so it's overridable per environment without code changes
SENTRY_WINDOW_LADDER = os.getenv(
    "SENTRY_WINDOW_LADDER", "age:-1h,age:-6h,age:-24h"
).split(",")

# why: per-window issue cap — extractor investigates one issue; Orchestrator decides which
SENTRY_QUERY_LIMIT = int(os.getenv("SENTRY_QUERY_LIMIT", "3"))

# why: app frame cap — framework/library frames are always stripped before handoff
SENTRY_STACK_FRAME_LIMIT = int(os.getenv("SENTRY_STACK_FRAME_LIMIT", "3"))

# why: shared status strings across all extractors — using constants prevents silent
# misspellings that would pass the wrong status to the Orchestrator
STATUS_COMPLETED = "completed"
STATUS_NO_DATA = "no_data"
STATUS_INJECTION_DETECTED = "injection_detected"

# why: Render API requires service ID and key from env — never hardcoded
RENDER_API_BASE = "https://api.render.com/v1"
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "")
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")

# why: guardrails for Render log extraction — Orchestrator overrides these per run
RENDER_LOG_FETCH_LIMIT = int(os.getenv("RENDER_LOG_FETCH_LIMIT", "500"))
RENDER_MAX_DISTINCT_ERRORS = int(os.getenv("RENDER_MAX_DISTINCT_ERRORS", "10"))
RENDER_LOG_MAX_MSG_LEN = int(os.getenv("RENDER_LOG_MAX_MSG_LEN", "300"))
