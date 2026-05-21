# Agent Test Scenarios — Aap ki Rasoi

**Purpose:** Acceptance criteria for every agent in Phase D and Phase E. An agent implementation is not complete until it produces a finding that matches the expected output for its relevant scenarios.

**Finding schema reference:** `agents/schemas/models.py` — Pydantic models are the source of truth for all YAML fields.

---

## How to Use This File

1. Introduce the bug described in the scenario (or confirm the existing state already matches).
2. Trigger the investigation as specified.
3. Run the relevant agent(s) directly (Phase D) or through the orchestrator (Phase E).
4. Compare the agent's YAML finding against the expected output here.
5. **Pass criteria:** all required fields present with correct values. Runtime values (timestamps, user counts, git SHAs) may vary — what must match is the structural shape and the `root_cause`, `affected_layer`, `confidence`, and `regression` conclusions.

**Note on agent-specific `findings` fields:** `BaseFinding` in `models.py` defines `metadata` and `interpretation`. The `findings` block for each agent (e.g. `BackendSentryFinding`, `DiagnosticFinding`) is defined when that agent is built in Phase D. The YAML examples below show the expected fields for those blocks — treat them as the spec the Phase D agent must satisfy.

---

## Scenario Index

| # | Name | Pattern Name | Trigger | Agents Invoked |
|---|---|---|---|---|
| 1 | Reservation failures | `reservation-validation-spike` | Automated (backend Sentry) | Backend Sentry → Diagnostic → Coding |
| 2 | Render cold start | `render-cold-start-503` | Automated (frontend Sentry) | Frontend Sentry → Render Logs → Diagnostic → Coding |
| 3 | Missing allergens | `missing-field-frontend-query` | Manual GitHub issue | Diagnostic → Coding |
| 4 | Wrong order total | `seed-data-price-error` | Manual GitHub issue | GitHub → Diagnostic → Coding |
| 5 | Schema drift | `graphql-schema-resolver-drift` | Automated (frontend Sentry) | Frontend Sentry → Diagnostic → Coding |

---

## Scenario 1 — Reservation Failures (Validation Bug)

**Pattern name:** `reservation-validation-spike`
**Affected layer:** backend

### Bug Introduction

Add a new Check 4 to `validate_reservation_time` in
`backend/services/reservation_service.py`, after the existing Check 3 block (line 55):

```python
# Check 4 — must be booked at least 2 hours in advance
if (dt - now).total_seconds() / 3600 > 2:  # BUG: should be <
    return error_response(
        "Reservations must be made at least 2 hours in advance",
        "TOO_LAST_MINUTE",
        422,
    )
```

The `>` operator rejects all reservations that are **more** than 2 hours away — the
opposite of the intent. This causes a 422 for virtually every valid booking.

**Verify the bug is active:** POST a valid reservation 3+ days in the future.
Expect 422 with `"TOO_LAST_MINUTE"`. Sentry backend project shows a spike in
`TOO_LAST_MINUTE` errors on `POST /api/reservations`.

### Trigger

Automated: `sentry-monitor-backend.yml` (C.1) detects error count above threshold on
`POST /api/reservations`. Creates a GitHub issue with labels
`needs-analysis` + `source:backend-sentry`. Orchestrator fires.

### Expected Agent Routing

```
Orchestrator
  └─ Backend Sentry Agent   (reads Sentry backend project)
  └─ Diagnostic Agent         (traces error code to source)
  └─ Coding Agent   (synthesises findings)
```

Render Logs Agent and GitHub Agent are **not** invoked — the signal is a Sentry
validation spike, not a startup event or a commit search.

### Expected Findings per Agent

#### Backend Sentry Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "backend-sentry"
  status: "completed"
  source: "sentry-backend"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: "<git-sha>"
  release_id_unresolvable: false
findings:
  error_type: "HTTPValidationError"
  error_message: "Reservations must be made at least 2 hours in advance"
  error_code: "TOO_LAST_MINUTE"
  endpoint: "POST /api/reservations"
  status_code: 422
  first_seen: "<ISO-timestamp>"
  last_seen: "<ISO-timestamp>"
interpretation:
  root_cause: "422 spike on POST /api/reservations — all requests rejected with TOO_LAST_MINUTE regardless of booking lead time"
  affected_layer: "backend"
  regression: true
```

*`error_code`, `endpoint`, and `status_code` are backend-specific fields added to
`BackendSentryFinding` in D.2.*

#### Diagnostic Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "codebase"
  status: "completed"
  source: "filesystem"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: null
  release_id_unresolvable: false
findings:
  symbol: "validate_reservation_time"
  file: "backend/services/reservation_service.py"
  line_range: "16–57"
  finding: "Check 4 uses operator > instead of <; rejects all reservations more than 2 hours away"
  fix_file: "backend/services/reservation_service.py"
  fix_description: "Change `> 2` to `< 2` in the advance-booking check"
interpretation:
  root_cause: "Inverted comparison operator in advance-booking check rejects all normal reservations"
  affected_layer: "backend"
  regression: true
```

### Expected Coding

```yaml
root_cause: "Inverted operator (>) in validate_reservation_time Check 4 rejects all reservations more than 2 hours in advance"
confidence: "high"
recommended_fix: "Change `> 2` to `< 2` in the TOO_LAST_MINUTE check in backend/services/reservation_service.py"
runbook_reference: "troubleshooting.md#reservation-validation-spike"
escalation_flag: false
```

### Cleanup

Remove Check 4 from `validate_reservation_time` (or correct the operator to keep the feature).

---

## Scenario 2 — Render Cold Start (503 on Wake-up)

**Pattern name:** `render-cold-start-503`
**Affected layer:** infrastructure

### Bug Introduction

No code change required. The Render free tier suspends the backend service after 15
minutes of inactivity. When the first request hits a suspended container, Render
returns a 503 while the service restarts (~15–30 seconds).

**Reproduce:** Leave the backend idle for 20+ minutes, then make any API call from the
frontend. The frontend receives a 503. Sentry frontend project captures this as a
network error.

### Trigger

Automated: `sentry-monitor-frontend.yml` (C.2) detects 503 errors on API requests.
Creates a GitHub issue with labels `needs-analysis` + `source:frontend-sentry`.
Orchestrator fires.

### Expected Agent Routing

```
Orchestrator
  └─ Frontend Sentry Agent   (identifies 503 pattern)
  └─ Render Logs Agent       (correlates with cold-start log)
  └─ Diagnostic Agent          (rules out a code regression)
  └─ Coding Agent
```

### Expected Findings per Agent

#### Frontend Sentry Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "frontend-sentry"
  status: "completed"
  source: "sentry-frontend"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "medium"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: "<git-sha>"
  release_id_unresolvable: false
findings:
  error_type: "NetworkError"
  error_message: "503 Service Unavailable"
  affected_file: "src/lib/apolloClient.ts"
  line_number: null
  affected_field: null
  graphql_mutation: null
  affected_user_count: <runtime value>
  first_seen: "<ISO-timestamp>"
  last_seen: "<ISO-timestamp>"
interpretation:
  root_cause: "503 errors on all API requests; burst pattern consistent with service wake-up, not application error"
  affected_layer: "infrastructure"
  regression: false
```

#### Render Logs Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "render-logs"
  status: "completed"
  source: "render-api"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: "render-cold-start-503"
  release_id: null
  release_id_unresolvable: false
findings:
  event_type: "cold_start"
  startup_duration_seconds: <15–30>
  log_lines:
    - "Starting server"
    - "Application startup complete"
  correlates_with_503_window: true
interpretation:
  root_cause: "Service woke from suspension; startup delay caused 503s during initialisation window"
  affected_layer: "infrastructure"
  regression: false
```

#### Diagnostic Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "codebase"
  status: "completed"
  source: "filesystem"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 0
  runbook_match: null
  release_id: null
  release_id_unresolvable: false
findings:
  symbol: null
  file: null
  finding: "No recent changes to request-path code (routes, middleware, services). 503s are not caused by a code regression."
interpretation:
  root_cause: "No application code change found; confirms infrastructure cause"
  affected_layer: "infrastructure"
  regression: false
```

### Expected Coding

```yaml
root_cause: "Render free tier cold start — service suspended after inactivity; startup delay produces 503s on first request"
confidence: "high"
recommended_fix: "Upgrade to Render Starter tier (no suspension) or add a keep-alive pinger hitting GET /health every 10 minutes"
runbook_reference: "troubleshooting.md#render-cold-start-503"
escalation_flag: false
```

### Cleanup

No code to revert. Add keep-alive or upgrade tier to prevent recurrence.

---

## Scenario 3 — Missing Allergens (Field Not in GraphQL Query)

**Pattern name:** `missing-field-frontend-query`
**Affected layer:** frontend

### Bug Introduction

The `allergens` field is defined in `src/features/menu/types.ts:12` and rendered in
`src/components/FoodItemModal.tsx`, but is absent from `MENU_QUERY` in
`src/features/menu/hooks/useMenu.ts`.

**This bug may already be present.** Verify by checking whether `allergens` appears in
`MENU_QUERY` — if it does not, no change is needed to reproduce it.

To introduce deliberately: ensure `allergens` is in the gateway schema and returned by
the resolver, then remove it from `MENU_QUERY`.

**Verify the bug is active:** Open the menu modal for any dish that has allergens in the
database. The allergen list is empty or null. No Sentry error fires — this is a silent
data gap, not a JavaScript exception.

### Trigger

Manual: A GitHub issue is opened: "Allergen information not showing on menu items".
Orchestrator is invoked via the `/troubleshoot` skill or by manually adding the
`needs-analysis` label.

### Expected Agent Routing

```
Orchestrator
  └─ Diagnostic Agent         (traces field through all layers)
  └─ Coding Agent
```

No Sentry agent — this is a silent data gap, not an exception. No Render Logs agent —
infrastructure is fine.

### Expected Findings per Agent

#### Diagnostic Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "codebase"
  status: "completed"
  source: "filesystem"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: null
  release_id_unresolvable: false
findings:
  symbol: "allergens"
  trace:
    - layer: "frontend-display"
      file: "src/components/FoodItemModal.tsx"
      status: "present"
    - layer: "frontend-type"
      file: "src/features/menu/types.ts"
      status: "present"
    - layer: "frontend-query"
      file: "src/features/menu/hooks/useMenu.ts"
      status: "missing"
    - layer: "gateway-schema"
      file: "graphql-gateway/schema.graphql"
      status: "present"
    - layer: "backend-resolver"
      file: "backend/"
      status: "present"
  finding: "allergens defined in types and displayed in UI but absent from MENU_QUERY; backend returns it but frontend never requests it"
interpretation:
  root_cause: "Frontend GraphQL query missing allergens field; field present at all other layers"
  affected_layer: "frontend"
  regression: true
```

### Expected Coding

```yaml
root_cause: "allergens missing from MENU_QUERY in useMenu.ts; field is available in the schema and returned by the resolver"
confidence: "high"
recommended_fix: "Add `allergens` to the items selection in MENU_QUERY in src/features/menu/hooks/useMenu.ts"
runbook_reference: "troubleshooting.md#missing-field-frontend-query"
escalation_flag: false
```

### Cleanup

Add `allergens` to `MENU_QUERY`.

---

## Scenario 4 — Wrong Order Total (Seed Data Price Error)

**Pattern name:** `seed-data-price-error`
**Affected layer:** backend

### Bug Introduction

In the menu item seed data, change the price of one item by shifting the decimal point
(e.g. £12.99 → £1299.00). This simulates a data-entry error that propagates to every
order containing that item.

**Seed data location:** Find the file via `grep -r "12.99" backend/` or check Alembic
migrations for seed inserts.

**Verify the bug is active:** The affected item shows the wrong price on the menu, and
order totals that include it are inflated.

### Trigger

Manual: A GitHub issue is opened: "Order total is wrong — item prices are incorrect".
Orchestrator is invoked via the `/troubleshoot` skill.

### Expected Agent Routing

```
Orchestrator
  └─ GitHub Agent     (looks for a recent commit touching price data)
  └─ Diagnostic Agent   (traces the price value from display to seed file)
  └─ Coding Agent
```

GitHub Agent runs first — if a recent commit touched the seed data, that commit is the
primary signal. Diagnostic Agent then confirms the exact wrong value and its location.

### Expected Findings per Agent

#### GitHub Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "github"
  status: "completed"
  source: "github-api"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: null
  release_id_unresolvable: false
findings:
  commit_sha: "<git-sha>"
  commit_message: "<commit message that introduced the price change>"
  files_changed:
    - "<path to seed data file>"
  diff_summary: "Price of <item name> changed from 12.99 to 1299.00"
interpretation:
  root_cause: "Recent commit introduced a decimal point error in seed data price"
  affected_layer: "backend"
  regression: true
```

#### Diagnostic Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "codebase"
  status: "completed"
  source: "filesystem"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: null
  release_id_unresolvable: false
findings:
  symbol: "price"
  trace:
    - layer: "frontend-display"
      file: "src/features/menu/"
      status: "displays value from GraphQL"
    - layer: "gateway"
      file: "graphql-gateway/"
      status: "passes through from backend"
    - layer: "backend-service"
      file: "backend/services/menu_service.py"
      status: "reads from database"
    - layer: "seed-data"
      file: "<path to seed data file>"
      status: "incorrect value: 1299.00"
  finding: "Price 1299.00 in seed data for <item name>; should be 12.99"
interpretation:
  root_cause: "Decimal point error in seed data; incorrect price propagates through all layers unchanged"
  affected_layer: "backend"
  regression: true
```

### Expected Coding

```yaml
root_cause: "Seed data price for <item name> set to 1299.00 (should be 12.99) introduced in commit <sha>"
confidence: "high"
recommended_fix: "Fix price in seed data file, write a corrective migration to update the existing row, and redeploy"
runbook_reference: "troubleshooting.md#seed-data-price-error"
escalation_flag: false
```

### Cleanup

Revert the price in the seed data and run a corrective migration.

---

## Scenario 5 — Schema Drift (Field in Query But Not in Schema)

**Pattern name:** `graphql-schema-resolver-drift`
**Affected layer:** gateway

### Bug Introduction

Add `preparation_time` to the items selection in `MENU_QUERY` in
`src/features/menu/hooks/useMenu.ts`:

```graphql
# Add to the items block inside MENU_QUERY:
preparation_time
```

This field does not exist in the gateway schema. Apollo rejects the query or returns
`null`, and any frontend code that reads `item.preparation_time` throws a TypeError
that Sentry captures.

**Verify the bug is active:** Load the menu page. Sentry frontend project shows a
TypeError or an Apollo "Cannot query field 'preparation_time'" error.

### Trigger

Automated: `sentry-monitor-frontend.yml` (C.2) detects a TypeError spike on the menu
page. Creates a GitHub issue with labels `needs-analysis` + `source:frontend-sentry`.
Orchestrator fires.

### Expected Agent Routing

```
Orchestrator
  └─ Frontend Sentry Agent   (identifies the unknown field error)
  └─ Diagnostic Agent          (traces the field through all layers)
  └─ Coding Agent
```

### Expected Findings per Agent

#### Frontend Sentry Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "frontend-sentry"
  status: "completed"
  source: "sentry-frontend"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: null
  release_id: "<git-sha>"
  release_id_unresolvable: false
findings:
  error_type: "TypeError"
  error_message: "Cannot query field 'preparation_time' on type 'MenuItem'"
  affected_file: "src/features/menu/hooks/useMenu.ts"
  line_number: null
  affected_field: "preparation_time"
  graphql_mutation: null
  affected_user_count: <runtime value>
  first_seen: "<ISO-timestamp>"
  last_seen: "<ISO-timestamp>"
interpretation:
  root_cause: "Frontend query requests preparation_time which is not defined in the gateway schema"
  affected_layer: "gateway"
  regression: true
```

#### Diagnostic Agent

```yaml
metadata:
  schema_version: "1.0"
  agent: "codebase"
  status: "completed"
  source: "filesystem"
  time_window:
    from_: "<ISO-timestamp>"
    to: "<ISO-timestamp>"
  confidence: "high"
  pii_flag: false
  injection_flag: false
  findings_count: 1
  runbook_match: "graphql-schema-resolver-drift"
  release_id: null
  release_id_unresolvable: false
findings:
  symbol: "preparation_time"
  trace:
    - layer: "frontend-query"
      file: "src/features/menu/hooks/useMenu.ts"
      status: "present (requested)"
    - layer: "gateway-schema"
      file: "graphql-gateway/schema.graphql"
      status: "missing"
    - layer: "backend"
      file: "backend/"
      status: "not applicable"
  finding: "preparation_time requested in frontend query but not defined in the gateway schema — schema-query drift"
  validate_schema_script: "scripts/validate-schema.js"
interpretation:
  root_cause: "Frontend query added a field that was never added to the GraphQL schema"
  affected_layer: "gateway"
  regression: true
```

### Expected Coding

```yaml
root_cause: "preparation_time in MENU_QUERY has no corresponding definition in the gateway schema (MenuItem type)"
confidence: "high"
recommended_fix: "Either (a) add `preparation_time: String` to MenuItem in the gateway schema and implement the resolver, or (b) remove the field from MENU_QUERY. Run validate-schema.js first to confirm the full scope of drift."
runbook_reference: "troubleshooting.md#graphql-schema-resolver-drift"
escalation_flag: false
```

### Cleanup

Remove `preparation_time` from `MENU_QUERY` in `useMenu.ts`.
