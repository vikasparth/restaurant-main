---
paths:
  - "backend/**/*.py"
---

## Testing Rules

### Writing test payloads
- Before writing any test payload helper, open the Pydantic model file and copy the exact field names. The model is the contract — not the spec, not memory.
- Before writing a new test file that calls an existing endpoint, read one existing test file for that endpoint first to get correct field names and payload structure.

### Writing SQL in services
- Before writing any SQL query, grep the migration files for the exact column names. Never assume — the spec and the schema often use different names (e.g. spec says `reservation_date`, schema has `reserved_date`).
- Before writing any `settings.<field>` reference, grep `core/config.py` for the exact field name. Never construct field names dynamically (e.g. `getattr(settings, f"monitor_{name}_threshold")`) — always use explicit references. A typo silently builds the wrong attribute name and only fails at runtime.

### Config values in tests
- Never hardcode a value in a test that the production code reads from `settings.*`.
- Import `settings` and use `settings.<field>` — the same source the route uses. This prevents drift when defaults change.
- Applies to: tokens (`settings.internal_token`), emails (`settings.owner_email`), phone numbers, environment flags — anything from `.env`.

### Mocking with `@patch`
- Always patch at the **import site** (where the function is used), not the **definition site**.
- If `notification_service.py` does `from services.email_service import send_email`, patch `services.notification_service.send_email` — not `services.email_service.send_email`.
- Rule of thumb: the patch path is `<module_that_calls_it>.<function_name>`.
