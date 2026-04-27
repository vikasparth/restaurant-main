# Logging Strategy

## Purpose

This document defines the logging standard for the Aap ki Rasoi backend.
It serves two audiences: a new engineer learning the codebase, and a GenAI
agent generating or debugging backend code. Both must be able to follow
these rules without ambiguity.

---

## The Stack

| Layer | What it does |
|---|---|
| Python `logging` module | Standard library logger — all code imports from here |
| `pythonjsonlogger` | Formats log lines as JSON in production, human-readable in dev |
| `RequestIdFilter` | Stamps every log line with `request_id` from the current request context |
| `setup_logging()` | Called once at startup in `main.py` — configures format and handler |

Every log line automatically carries: `asctime`, `levelname`, `name` (module),
`message`, `request_id`. You never add these manually.

---

## Import Pattern

Every file that needs a logger uses this exact pattern:

```python
import logging                              # stdlib — always first import group

logger = logging.getLogger(__name__)       # module-level, after imports
```

`__name__` gives each module its own logger name (e.g. `routers.orders`,
`services.order_service`), which appears in the `name` field of every log line.

---

## Layer Rules

### Routers — exception logging only

Routers log failures. They do not log success — the middleware already records
every request with method, path, status code, and duration.

```python
except Exception as e:
    logger.exception("[orders] failed to create order")
    return JSONResponse(status_code=503, ...)
```

Rules:
- Always use `logger.exception()` — captures full stack trace automatically
- Message format: `[router_name] failed to <operation>` — name the operation,
  never just "unexpected error"
- No `extra={}` needed — routers are infrastructure, not business events

### Core Business Services — success events

Every service function that creates a business record must log a success event
with the reference number. This is the audit trail.

```python
logger.info(
    "[orders] order created — reference: %s", reference,
    extra={"event": "order_created", "reference": reference}
)
```

Rules:
- Use both prose (human-readable in Render) and `extra={}` (machine-parseable
  for GenAI agents and structured log queries)
- Always include `reference` in `extra` when one exists
- `event` field uses snake_case: `order_created`, `reservation_confirmed`,
  `catering_order_created`

### Downstream Services — success after external calls

Services that call external APIs (email, WhatsApp) log success after each call.

```python
logger.info("WhatsApp sent to owner — %d chars", len(body))
logger.info("Email sent to %s — subject: %s", to, subject)
```

Rules:
- Prose only — no `extra={}` needed (no reference number at this layer)
- Never log the full recipient email in production — partial logging is fine
  if needed for debugging (see PII rules below)

### Notification Service — failures per channel

Log each channel failure individually with the reference number so you can
tell exactly which channel failed for which business event.

```python
logger.error(
    "[notifications] order customer email failed — reference: %s: %s",
    reference, e
)
```

### Middleware — do not add logging here

Request/response logging is already handled by `RequestLoggingMiddleware`.
Do not add logger calls inside middleware — it runs on every request and
any mistake here affects all routes.

---

## Log Structure Reference

| Field | Source | Present in |
|---|---|---|
| `asctime` | Automatic | All lines |
| `levelname` | Automatic | All lines |
| `name` | `getLogger(__name__)` | All lines |
| `request_id` | `RequestIdFilter` | All lines |
| `message` | Your log call | All lines |
| `event` | `extra={"event": ...}` | Business events only |
| `reference` | `extra={"reference": ...}` | Business events only |

**Good log message — router error:**
```
[orders] failed to create order
```

**Good log message — business event:**
```
[orders] order created — reference: AKR-20260414-0012
extra: {"event": "order_created", "reference": "AKR-20260414-0012"}
```

**Bad log message:**
```
unexpected error        ← no router prefix, no operation name
error occurred: {e}     ← use logger.exception(), not logger.error() with {e}
order placed            ← no reference number, no extra fields
```

---

## What Never to Log

- Query parameters — can contain customer PII (`?email=...`, `?name=...`)
- Request bodies — contain customer names, emails, phone numbers, order details
- Full recipient email addresses in infrastructure or middleware logs
- Stack dumps in the message string — use `logger.exception()` which handles this

---

## Output Format

| Environment | Format | Why |
|---|---|---|
| Production (`IS_PRODUCTION=true`) | JSON — parsed by Render log viewer | Structured queries, Render log search |
| Local dev | Human-readable | Easy to read in terminal |

Controlled by `setup_logging()` in `core/logging.py` — no code changes needed.

---

## Sentry (coming)

Sentry will be added as part of task 3.7 / 3.14 / 3.16.9. It will automatically
capture every `logger.exception()` call with full stack trace and request context.
No changes to existing log calls will be needed — Sentry integrates with the
standard Python `logging` module via a log handler.
