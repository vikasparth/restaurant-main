# Spec — Task 3.13: MCP Server for Monitor Skills

> Builds the MCP server that gives all monitor skills (orchestrator and
> sub-skills) access to automated tool calls. The orchestrator routing
> table and sub-skill logic are unchanged — only the data-fetching steps
> swap from file reads / curl / asyncpg scripts to MCP tool calls.
> See ADR-0008 for the skill architecture this server supports.

---

## What it is

A FastMCP server (`backend/mcp_server.py`) exposing 6 tools that the
monitor sub-skills call during a health check session. Once deployed,
Render log health becomes part of the automatic summary — no manual
copy-paste needed.

No new routes. No migrations. No schema changes.

---

## Prerequisites (must be in place before implementation)

| Config key | Where | Notes |
|---|---|---|
| `RENDER_API_KEY` | `backend/.env` | Each engineer generates their own from Render → Account Settings → API Keys |
| `RENDER_SERVICE_ID` | `backend/.env` | `srv-d7eq668sfn5c738gk2g0` |
| `RENDER_OWNER_ID` | `backend/.env` | `tea-d7a5r695pdvs73c0suf0` |
| `RENDER_API_BASE_URL` | `config.py` default | `https://api.render.com/v1` — override in `.env` only if Render changes their API version |
| `PRODUCTION_URL` | `config.py` default | `https://restaurant-main.onrender.com` — override in `.env` only if service URL changes |
| `GITHUB_TOKEN` | `backend/.env` | Optional — only needed when repo is private |
| `GITHUB_REPO` | `backend/.env` | `vikasparth/restaurant-main` |
| `DATABASE_URL` | `backend/.env` | Already present |

All config fields are already added to `backend/core/config.py`.

---

## File Structure

```
backend/
    mcp_server.py          ← FastMCP server entry point
    tools/
        __init__.py
        health.py          ← check_health_endpoint
        render_logs.py     ← get_render_logs
        github_commits.py  ← get_recent_commits
        db_queries.py      ← query_request_logs, query_notification_failures
        provider_status.py ← check_provider_status
```

---

## Tool Definitions

### `check_health_endpoint()`

Calls `GET {settings.production_url}/health`.

Returns:
```json
{ "status": "reachable", "http_code": 200 }
{ "status": "unreachable", "http_code": 503, "error": "..." }
```

Used by: orchestrator (Step 1), monitor-db (Check 1).

---

### `get_render_logs(lines: int = 100)`

Calls `GET {settings.render_api_base_url}/logs` with:
- `ownerId`: `settings.render_owner_id`
- `resource`: `settings.render_service_id`
- `limit`: `lines` (max 100)
- Auth: `Bearer settings.render_api_key`

Returns: list of log lines (timestamp, message, level).

Used by: monitor-server (Check 3) — replaces manual engineer copy-paste.

**Key upgrade:** once available, monitor-server Check 3 switches from
"ask engineer to paste logs" to "call get_render_logs() and analyse
automatically."

---

### `get_recent_commits(count: int = 5)`

Calls GitHub API:
- Public repo: `GET https://api.github.com/repos/{GITHUB_REPO}/commits`
- Private repo: same endpoint with `Authorization: Bearer {GITHUB_TOKEN}`

Returns: list of `{ sha, message, author, committed_at }`.

Used by: monitor-server (Check 2) — replaces `git log --oneline -5`.

**Why remote instead of local git:** other engineers on the team may not
have the repo checked out locally. Render deploys from the remote — the
remote is the authoritative source for deploy history.

---

### `query_request_logs(window_hours: int = 12)`

Queries `request_logs` using `DATABASE_URL`:

```sql
SELECT path,
       ROUND(AVG(duration_ms)) AS avg_ms,
       MAX(duration_ms) AS max_ms,
       COUNT(*) AS requests
FROM request_logs
WHERE created_at > NOW() - INTERVAL '{window_hours} hours'
GROUP BY path
ORDER BY avg_ms DESC
LIMIT 10
```

Returns: list of `{ path, avg_ms, max_ms, requests }`.

Used by: monitor-db (Check 2).

---

### `query_notification_failures(window_hours: int = 12)`

Queries `notification_logs` using `DATABASE_URL`:

```sql
SELECT provider, error_code, COUNT(*) AS failures
FROM notification_logs
WHERE success = false
  AND created_at > NOW() - INTERVAL '{window_hours} hours'
GROUP BY provider, error_code
ORDER BY failures DESC
```

Returns: list of `{ provider, error_code, failures }`.

Used by: monitor-dependencies (Check 2).

---

### `check_provider_status(provider: str)`

Fetches provider status pages using URLs from config:
- `resend` → `settings.resend_status_url` (default: `https://resend-status.com/`)
- `twilio` → `settings.twilio_status_url` (default: `https://status.twilio.com/`)

Returns the raw status text scraped from the provider's status page —
do not normalise to fixed values. Claude interprets the text directly.

```json
{ "provider": "resend", "raw_status": "All systems operational" }
{ "provider": "twilio", "raw_status": "SMS, Latin America — Degraded Performance" }
```

Used by: monitor-dependencies (Check 1) — replaces WebFetch calls.

---

## Sub-skill Changes After 3.13

| Sub-skill | Before (3.12) | After (3.13) |
|---|---|---|
| monitor-check Step 1 | `curl /health` | `check_health_endpoint()` |
| monitor-server Check 2 | `git log --oneline -5` | `get_recent_commits()` |
| monitor-server Check 3 | Ask engineer to paste logs | `get_render_logs()` — automatic |
| monitor-db Check 1 | `curl /health` | `check_health_endpoint()` |
| monitor-db Check 2 | asyncpg script | `query_request_logs()` |
| monitor-dependencies Check 1 | WebFetch status pages | `check_provider_status()` |
| monitor-dependencies Check 2 | asyncpg script | `query_notification_failures()` |

The orchestrator routing table is unchanged.

---

## MCP Server Registration

Register via Claude Code CLI — this resolves the path correctly for each
engineer's machine rather than hardcoding an absolute path in the file:

```bash
claude mcp add monitor python backend/mcp_server.py
```

This writes an absolute path entry to `.claude/settings.json` scoped to
this project. Each engineer runs this once after cloning the repo.

The MCP server reads all secrets (`RENDER_API_KEY`, `DATABASE_URL`, etc.)
from `backend/.env` at startup — no secrets in `settings.json`.

---

## Out of Scope

- No new API routes
- No database migrations
- No frontend changes
- Sentry integration — task 3.14
