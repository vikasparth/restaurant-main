---
paths:
  - "backend/**/*.py"
---

## Pydantic Model Config Rules

- **All request models must use `extra="forbid"`** — this turns silent data loss (typo'd optional fields silently dropped) into a loud 422 error.
- **Response models and third-party wrapper models use the default (`extra="ignore"`)** — external APIs add new fields in minor versions; breaking on unknown fields would be fragile.
- Always import `ConfigDict` from `pydantic` and set `model_config` as the first line inside the class, before any fields.

```python
# ✅ request model — strict
class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ...

# ✅ third-party response wrapper — resilient
class StripeWebhookPayload(BaseModel):
    # extra="ignore" is the default — no config needed
    ...
```

## Exception Handling Rules

- **Always use `except Exception as e`** — never bare `except Exception:`. Without `as e` the error is invisible in the debugger and in logs.
- **Always log the exception before returning a generic response** — `logger.exception("[router_name] unexpected error")`. This captures the full stack trace and `request_id` automatically. Without this a 503 in production leaves no trace — the only signal is a status code with no root cause. See `docs/engineering-practices/logging-strategy.md` for the full logging strategy.
- **Never swallow exceptions silently in service calls** — if a service raises, let it propagate to the router where it gets logged and handled consistently.

```python
# ✅ correct pattern
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.exception("[menu] unexpected error")
    return JSONResponse(status_code=503, content={...})

# ❌ wrong — error invisible in debugger and Render logs
except Exception:
    return JSONResponse(status_code=503, content={...})
```
