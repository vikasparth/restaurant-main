from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# why: load agents/.env before reading any os.getenv() calls below —
# override=False means vars already set in the shell (CI, Render) take precedence
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

_SONNET = "claude-sonnet-4-6"
_HAIKU = "claude-haiku-4-5-20251001"

ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", _SONNET)
RECOMMENDATION_MODEL = os.getenv("RECOMMENDATION_MODEL", _SONNET)
CODEBASE_MODEL = os.getenv("CODEBASE_MODEL", _SONNET)
FRONTEND_SENTRY_MODEL = os.getenv("FRONTEND_SENTRY_MODEL", _HAIKU)
BACKEND_SENTRY_MODEL = os.getenv("BACKEND_SENTRY_MODEL", _HAIKU)
RENDER_LOGS_MODEL = os.getenv("RENDER_LOGS_MODEL", _HAIKU)
GITHUB_MODEL = os.getenv("GITHUB_MODEL", _HAIKU)
SENTRY_API_BASE = os.getenv("SENTRY_API_BASE", "https://sentry.io/api/0")

AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "5"))
AGENT_MAX_TOKENS_PER_TURN = int(os.getenv("AGENT_MAX_TOKENS_PER_TURN", "1024"))

FRONTEND_SENTRY_MAX_TURNS = int(os.getenv("FRONTEND_SENTRY_MAX_TURNS", str(AGENT_MAX_TURNS)))
FRONTEND_SENTRY_MAX_TOKENS = int(os.getenv("FRONTEND_SENTRY_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

BACKEND_SENTRY_MAX_TURNS = int(os.getenv("BACKEND_SENTRY_MAX_TURNS", str(AGENT_MAX_TURNS)))
BACKEND_SENTRY_MAX_TOKENS = int(os.getenv("BACKEND_SENTRY_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

RENDER_LOGS_MAX_TURNS = int(os.getenv("RENDER_LOGS_MAX_TURNS", str(AGENT_MAX_TURNS)))
RENDER_LOGS_MAX_TOKENS = int(os.getenv("RENDER_LOGS_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

GITHUB_MAX_TURNS = int(os.getenv("GITHUB_MAX_TURNS", str(AGENT_MAX_TURNS)))
GITHUB_MAX_TOKENS = int(os.getenv("GITHUB_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

CODEBASE_MAX_TURNS = int(os.getenv("CODEBASE_MAX_TURNS", "8"))
CODEBASE_MAX_TOKENS = int(os.getenv("CODEBASE_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))

RECOMMENDATION_MAX_TURNS = int(os.getenv("RECOMMENDATION_MAX_TURNS", "1"))
RECOMMENDATION_MAX_TOKENS = int(os.getenv("RECOMMENDATION_MAX_TOKENS", str(AGENT_MAX_TOKENS_PER_TURN)))


