# Backend Rules — Restaurant Management System

## Slice Rules (Backend)

The backend dependency map is at **`backend/specs/DEPENDENCY_MAP.md`**. Apply the generic slice rules from the root `CLAUDE.md` using this file as the layer's map.

## Backend Expectations
- Backend lives only in main_project.
- Do not generate backend code inside lovable_project.

## Authentication — Required Everywhere
- **Every protected route MUST have authentication middleware.** No exceptions.
- Apply auth guards on:
  - All admin pages and dashboard routes
  - All API routes that read or write data
  - Any route that involves user-specific data (orders, reservations, profiles)
- Use role-based access control (RBAC) where different user types exist (e.g. admin, staff, customer).
- Auth tokens must be stored securely (httpOnly cookies preferred over localStorage).
- Always validate the session/token on the server side — never trust client-side auth state alone.
- Add an auth layer to the API service wrapper so every request automatically includes credentials.

## Logging Rules — Design for the Developer First

When writing logs, always ask: *what does a developer (or AI agent) debugging a 2am incident need to find the root cause fast?* Every log line should make it faster to answer:
1. Which request failed? (correlation ID)
2. What went wrong? (error message + context)
3. Why? (relevant state, not a stack dump)

- **Always include `request_id` (correlation ID)** in every log line — generated per request in middleware, stored in `contextvars.ContextVar`, read automatically by the logger. One ID → one search → all lines for that request.
- **Never log query parameters** — they can contain customer PII (e.g. `?email=...`, `?name=...`).
- **Never log request bodies or headers** in middleware or shared infrastructure — bodies contain customer names, emails, phone numbers, and order details.
- Infrastructure logs (middleware): method, path (no query string), status code, duration ms, request_id. Nothing else.
- Business event logs: keyed by reference number (e.g. `{"event": "order_created", "reference": "AKR-20260414-0012", "request_id": "..."}`) — never contain raw PII.

## Service Layer Rules

- **Routes must not call service internals directly.** If a service has an orchestrator function (e.g. `run_monitor`), the route calls the orchestrator — not the individual functions it wraps. Bypassing the orchestrator breaks encapsulation and causes steps (like sending email) to be silently skipped.
- Routes are responsible for: auth, input validation, calling the service layer, returning the response.
- Services are responsible for: business logic, orchestration, external calls (DB, email, GitHub, etc.).

## Adding New Packages to requirements.txt

When adding a new package:
1. `pip install <package>` in the venv — pip silently upgrades existing packages to satisfy dependencies.
2. Run `pip show <package>` immediately after and check the `Requires:` field.
3. For every dependency listed there, check the version now installed in the venv (`pip show <dep>`) and update `requirements.txt` to match.
4. Verify locally: `pip install -r requirements.txt` must complete with no conflicts before committing.

**Why this matters:** pip upgrades packages in the venv automatically but does not update `requirements.txt`. Render installs fresh from `requirements.txt`, so pinned versions that were silently upgraded locally will cause a build conflict on Render.

## Config / Environment Rules

- **Always update `config.py` and `.env` together.** Adding a new env var means adding the matching field to `Settings` in the same step — never one without the other.
- The `Settings` field name must match the env var name exactly (pydantic-settings is case-insensitive, but use the same spelling). Mismatches silently fall back to the default with no error.
- After adding a field, verify it by printing `settings.<field>` or checking it in a test — silent defaults are hard to spot.

---

## Pre-Commit Checklist (Backend)
Before every commit touching backend code, ALL of the following must pass:

1. **Tests** — `pytest` (no failing tests)
2. **Format check** — `black --check .` (no unformatted files)
3. **Lint** — `flake8` (zero warnings allowed)
