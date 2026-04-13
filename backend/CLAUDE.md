# Backend Rules — Restaurant Management System

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

## Config / Environment Rules

- **Always update `config.py` and `.env` together.** Adding a new env var means adding the matching field to `Settings` in the same step — never one without the other.
- The `Settings` field name must match the env var name exactly (pydantic-settings is case-insensitive, but use the same spelling). Mismatches silently fall back to the default with no error.
- After adding a field, verify it by printing `settings.<field>` or checking it in a test — silent defaults are hard to spot.

## Testing Rules

### Writing test payloads
- Before writing any test payload helper, open the Pydantic model file and copy the exact field names. The model is the contract — not the spec, not memory.
- Before writing a new test file that calls an existing endpoint, read one existing test file for that endpoint first to get correct field names and payload structure.

### Writing SQL in services
- Before writing any SQL query, grep the migration files for the exact column names. Never assume — the spec and the schema often use different names (e.g. spec says `reservation_date`, schema has `reserved_date`).

### Config values in tests
- Never hardcode a value in a test that the production code reads from `settings.*`.
- Import `settings` and use `settings.<field>` — the same source the route uses. This prevents drift when defaults change.
- Applies to: tokens (`settings.internal_token`), emails (`settings.owner_email`), phone numbers, environment flags — anything from `.env`.

### Mocking with `@patch`
- Always patch at the **import site** (where the function is used), not the **definition site**.
- If `notification_service.py` does `from services.email_service import send_email`, patch `services.notification_service.send_email` — not `services.email_service.send_email`.
- Rule of thumb: the patch path is `<module_that_calls_it>.<function_name>`.

---

## Pre-Commit Checklist (Backend)
Before every commit touching backend code, ALL of the following must pass:

1. **Tests** — `pytest` (no failing tests)
2. **Format check** — `black --check .` (no unformatted files)
3. **Lint** — `flake8` (zero warnings allowed)
