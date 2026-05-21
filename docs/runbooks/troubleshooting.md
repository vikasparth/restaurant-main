# Troubleshooting Runbook — Aap ki Rasoi

**Audience:** On-call engineers and the Diagnostic Agent. Each entry covers one named error pattern: what it looks like, why it happens, how to investigate, and when to escalate.

**This is not a test spec.** For expected agent output, see `docs/agent-test-scenarios.md`.

---

## Pattern Index

| Pattern name | Affected layer | Typical trigger |
|---|---|---|
| [reservation-validation-spike](#reservation-validation-spike) | backend | Backend Sentry 422 spike |
| [render-cold-start-503](#render-cold-start-503) | infrastructure | Frontend Sentry 503 burst |
| [missing-field-frontend-query](#missing-field-frontend-query) | frontend | Manual GitHub issue |
| [seed-data-price-error](#seed-data-price-error) | backend | Manual GitHub issue |
| [graphql-schema-resolver-drift](#graphql-schema-resolver-drift) | gateway | Frontend Sentry TypeError |

---

## reservation-validation-spike

**Affected layer:** backend

### Symptoms

- Spike in 422 responses on `POST /api/reservations` in the backend Sentry project
- Error code `TOO_LAST_MINUTE` in the response body — not a server crash, a deliberate rejection
- All or nearly all reservation attempts fail regardless of booking date

### Likely cause

A comparison operator in `validate_reservation_time` is inverted, causing the guard clause to reject valid bookings instead of only rejecting last-minute ones.

### Investigation steps

1. In the backend Sentry project, filter by `TOO_LAST_MINUTE` — note first seen timestamp and error count trend (sudden spike vs gradual rise)
2. Open `backend/services/reservation_service.py` and find `validate_reservation_time`
3. Grep for `TOO_LAST_MINUTE` — locate the exact guard clause that returns this code
4. Read the surrounding condition: check whether the operator (`>` / `<`) matches the intent ("reject if less than 2 hours away" means `<`, not `>`)
5. If the operator looks correct, fall back to timeline: find the commit or deployment made just before the error spike started and diff that file

### Escalation criteria

Escalate (`escalation_flag: true`) if:
- The error predates the current release by more than one deploy (not a fresh regression — may have been silently failing longer)
- `validate_reservation_time` is called from more than one endpoint (wider blast radius)

---

## render-cold-start-503

**Affected layer:** infrastructure

### Symptoms

- Short burst of 503 errors across all API endpoints in the frontend Sentry project — not isolated to one route
- Errors clear within 30–60 seconds without any code change or deploy
- No corresponding exception in backend Sentry (the service was suspended, not crashing)

### Likely cause

Render free tier suspends the backend container after 15 minutes of inactivity. The first request during wake-up receives a 503 while the service restarts (~15–30 seconds). This is a platform behaviour, not a code regression.

### Investigation steps

1. Check the Sentry error time window — a cold start produces a tight burst (under 60 seconds); an ongoing 503 spike suggests a crash or deploy failure, not a cold start
2. Note which endpoints are affected — if errors span all routes equally, the service was unavailable, not a specific handler failing
3. Fetch Render log events for the overlapping time window — look for `"Starting server"` and `"Application startup complete"` log lines
4. Confirm the Render startup timestamps fall inside the Sentry 503 window — if they align, the cause is confirmed
5. Check for recent commits to request-path code (`backend/routes/`, `backend/main.py`, middleware) — if none, there is no code regression to investigate

### Escalation criteria

Escalate (`escalation_flag: true`) if:
- 503s persist beyond 60 seconds after the first request (suggests a startup crash, not a suspension)
- Render logs show no `"Starting server"` entry — service may have crashed rather than suspended
- Errors recur multiple times per hour (cold starts happen at most once per 15-minute idle window)

---

## missing-field-frontend-query

**Affected layer:** frontend

### Symptoms

- A field renders as empty or null in the UI for all users (e.g. allergen list always blank)
- No Sentry error fires — the frontend receives a valid GraphQL response, the field is simply absent
- Reported via user complaint or manual GitHub issue, not automated monitoring

### Likely cause

The field is defined in the TypeScript types and rendered in the component, but was never added to the GraphQL query. The backend returns it, but the frontend never requests it — so it is silently omitted from every response.

### Investigation steps

1. From the GitHub issue, identify the missing field name
2. Grep for the field in `src/components/` — confirm it is referenced in the UI render code
3. Check `src/features/menu/types.ts` — confirm the TypeScript type includes the field
4. Grep for the field in `src/features/menu/hooks/useMenu.ts` — if it is absent from the query selection, that is the gap
5. Check `graphql-gateway/schema.graphql` — confirm the field exists in the schema (if missing here too, the scope is wider — see escalation)
6. Confirm the backend resolver returns the field — if present at all other layers but missing only from the query, the fix is a one-line query change

### Escalation criteria

Escalate (`escalation_flag: true`) if:
- The field is also absent from the gateway schema — a schema update is required before any frontend change, and schema changes need a coordinated deploy
- The field is absent from the backend resolver — three layers need changes, fix order matters (backend → schema → query)

---

## seed-data-price-error

**Affected layer:** backend

### Symptoms

- One or more menu items display the wrong price; order totals including that item are inflated
- No Sentry error fires — the wrong value is served correctly through all layers
- Reported via user complaint or manual GitHub issue

### Likely cause

A decimal point error in seed data or an Alembic migration introduced the wrong value (e.g. £12.99 → £1299.00). Every layer from database to UI passes the value through unchanged, so the error is invisible until a human notices the price.

### Investigation steps

1. From the GitHub issue, identify the affected item name and the wrong price value
2. Grep for the wrong value in `backend/` — check seed data files and Alembic migration files
3. Run `git log --oneline` scoped to seed/migration files — find the commit that introduced the wrong value; check the diff for the exact change
4. Trace the price top-down: seed file → `backend/services/menu_service.py` (reads from DB) → GraphQL resolver (passes through) → frontend display — confirm no transformation at any layer
5. Determine whether the wrong value exists only in code (seed file not yet applied) or has already been written to the database via a migration

### Escalation criteria

Escalate (`escalation_flag: true`) if:
- The wrong value was applied to the production database via a migration — a corrective `UPDATE` migration is required, not just a code fix; this needs a coordinated deploy
- Multiple items are affected — suggests a systematic data-entry error, not a one-off typo

---

## graphql-schema-resolver-drift

**Affected layer:** gateway

### Symptoms

- TypeError in the frontend Sentry project with message pattern: `"Cannot query field 'X' on type 'Y'"`
- Error fires on page load for all users visiting the affected page — not user-specific
- Stack trace points to a frontend hook file (e.g. `src/features/menu/hooks/useMenu.ts`)

### Likely cause

A field was added to a frontend GraphQL query but was never added to the gateway schema. Apollo rejects the query at the gateway before it reaches the backend.

### Investigation steps

1. From the Sentry error message, extract the unknown field name (e.g. `preparation_time`)
2. Grep for the field in `src/features/menu/hooks/useMenu.ts` — confirm it is present in the query selection
3. Grep for the field in `graphql-gateway/schema.graphql` — if absent, that is the drift point
4. Grep for the field in backend resolver files — determine whether the backend already returns this value (schema just wasn't updated) or the field does not exist at any layer
5. Run `scripts/validate-schema.js` to check whether additional fields are also out of sync beyond the one named in the error

### Escalation criteria

Escalate (`escalation_flag: true`) if:
- The field is also absent from the backend resolver — fix order matters (implement backend → add to schema → add to query), and the deploy must be sequenced; a partial fix will surface a different error
- `scripts/validate-schema.js` reports more than one drifted field — schema and codebase have diverged more broadly
