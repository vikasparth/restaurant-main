# API Integration Test Coverage

You have been asked to produce a comprehensive unit test plan for an API integration.

This skill covers every failure mode a downstream API can return. It applies to any HTTP API client — REST, GraphQL, or otherwise — regardless of language or framework.

---

## Step 1 — Identify the Integration

Read the spec or code file the user has indicated. Extract:

- **API being called** — name and base URL
- **Authentication mechanism** — API key, Bearer token, OAuth, Basic Auth, or none
- **Endpoints used** — list each `METHOD /path` the integration calls
- **Input contract** — what parameters or payload does the client send (guardrails, request body, query params)
- **Expected response shape** — what fields does the client read from the response
- **Existing test count** — how many tests already exist in the spec or test file

State these back to the user in a short summary before proceeding. If any are unclear, ask one question to resolve it.

---

## Step 2 — Generate the Test Plan

Produce a test plan table covering **all categories** below. Categories 1–8 are mandatory for every API integration. Category 9 (Pagination) is mandatory when the API returns paginated responses — skip it only if the API never paginates. Generate specific test names and descriptions, not generic placeholders.

### Category 1 — Happy Path
- Successful response with data → expected `status`, correct field values, correct counts
- Successful response with zero results → `no_data` or equivalent empty state

### Category 2 — Input Validation (before any HTTP call)
For each input parameter:
- Wrong type (e.g. `int` expected, `str` passed)
- Out-of-range value (e.g. negative count, zero limit)
- Malformed format (e.g. invalid SHA, bad date string, illegal characters)
- Missing required field

All input validation tests must assert **no HTTP call was made** — validation must run before the network.

### Category 3 — Authentication
- Missing credentials (empty token, no API key) → no HTTP call made
- Credentials present but rejected by API (401) → distinct status from authorization failure

### Category 4 — Authorization
- Credentials valid but insufficient permissions (403) → distinct status from authentication failure
- Scope or role missing for the specific endpoint

Authentication and Authorization must be **separate statuses** so the caller can react differently (expired token vs. wrong permissions).

### Category 5 — Resource Not Found
- API returns 404 → covers wrong repo, wrong ID, deleted resource, typo in config

### Category 6 — Rate Limiting and Throttling
- API returns 429 → `rate_limited` status; assert no retry attempt inside the extractor (retries are the Orchestrator's job)

### Category 7 — Server and Network Failures
- API returns 5xx → `server_error` status (transient, retry at caller level)
- `requests.Timeout` (or equivalent) raised → `timeout` status (distinct from connection failure — server reachable but slow)
- `requests.ConnectionError` (or equivalent) raised → `network_error` status (server unreachable)

Timeout and network error must be **separate statuses** — timeout implies the server is up but overloaded; network error implies it is unreachable.

### Category 8 — Response Schema Validation
- Response is missing an expected field (e.g. `author.login`, `data.items`) → `schema_error`
- Response field has wrong type (e.g. array expected, null returned) → `schema_error`
- Schema validation must run **after** a successful HTTP response, before any field access

### Category 9 — Pagination *(include when the API returns paginated responses)*

**Correctness:**
- Single page — all results fit in one request → no extra page fetched, all items returned
- Multi-page — results span multiple pages → all pages fetched and combined correctly
- Partial last page — final page has fewer items than `per_page` → items are not dropped

**Cap / boundary:**
- `max_items` exactly equals total results → stops cleanly, no extra page fetched
- `max_items` reached before all pages are exhausted → stops at cap, does not over-fetch
- Platform `per_page` limit exceeded (e.g. GitHub caps `per_page` at 100) → if single-page design, `max_items > platform_limit` must return `invalid_input` with no HTTP call; if multi-page design, assert correct number of page requests are made

**Fault tolerance:**
- Error on page 1 → existing Category 7 tests cover this
- Error on a subsequent page (page 1 succeeds, page N fails) → document the contract: does the extractor return partial results or a failure status? Test whichever the spec mandates
- Infinite loop guard → if the implementation follows `next` links, assert the loop is bounded by `max_items` and terminates even if the API keeps returning a `next` link

---

## Step 3 — Present the Full Test Table

Output a numbered markdown table with columns:

| # | Test name | Category | What it verifies |

Rules for test names:
- Use `snake_case`
- Start with `test_`
- Name must describe the scenario, not the assertion (e.g. `test_missing_token_returns_unauthenticated`, not `test_auth_failure`)
- Each test name must be unique and unambiguous

---

## Step 4 — Gap Check

After presenting the table, explicitly ask:

> "Are there any API-specific failure modes for **[API name]** not covered above? For example: partial responses, async job timeouts, webhook delivery failures, or API version mismatches."

Wait for the user's answer before marking the plan complete.

---

## Step 5 — Update the Spec

Once the user confirms the test plan is complete:

1. Add or replace the TDD Test Plan section in the spec file with the full numbered table
2. Add or replace the Exit Conditions table with one row per status
3. Update the acceptance criteria test count
4. Add any new status constants needed to the project's config file (never hardcode status strings in tests or implementation)

Do **not** write any test code or implementation code — this skill produces the plan only. Writing the tests is the next step and follows pair programming rules.

---

## What this skill does NOT do

- It does not write test code
- It does not write implementation code
- It does not make assumptions about which failures "probably won't happen" — categories 1–8 are always required; Category 9 is required when the API paginates
- It does not collapse Authentication and Authorization into one test or one status
- It does not collapse Timeout and NetworkError into one test or one status
