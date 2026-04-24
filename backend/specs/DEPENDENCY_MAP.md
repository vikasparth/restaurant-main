# Slice Dependency Map
**Read this before writing any new spec.**
For each slice, this tells you: which earlier slices to pull signatures from.

---

## Quick Reference

| Slice being written | Must pull signatures from |
|---|---|
| Slice 1 — Menu (Read) | None |
| Slice 2 — Delivery Validation | None |
| Slice 3 — Orders | Slice 1 (`validate_menu_items`), Slice 2 (`validate_zip`) |
| Slice 4 — Reservations | None |
| Slice 5 — Catering | Slice 1 (`validate_menu_items`, `MenuItem.catering_available`) |
| Slice 6 — Notifications | Slice 3, 4, 5 (wires into their services — read all three) |
| Slice 7 — Menu Admin CRUD | Slice 1 (extends `menu_service.py` — must not break existing signatures) |
| Slice 8 — Admin Endpoints | Slice 3, 4, 5, 7 (reads from all their services) |

---

## Shared Services (always inject when the slice uses them)

| Service | Full signature | Used by slices |
|---|---|---|
| DB connection | `async def get_db() -> AsyncGenerator` — use as FastAPI dependency | All |
| Location ID | `settings.default_location_id: str` from `core/config.py` | All |
| Restaurant config | `async def get_restaurant_config(db) -> dict` — keys: `operating_hours`, `timezone`, `min_order_amount`, `delivery_fee`, `max_reservation_party_size`, `catering_min_order`, `catering_deposit_percent` | 3, 4, 5, 8 |
| Reference number | `async def generate_reference_number(db) -> str` — returns `"AKR-YYYYMMDD-XXXX"` | 3, 4, 5 |
| Timezone | `def now_in_restaurant_time(tz: str) -> datetime` — returns current time as aware datetime in restaurant tz | 3, 4, 5 |
| Menu validation | `async def validate_menu_items(db, item_ids: list[str]) -> None` — raises `422 INVALID_MENU_ITEM` if any ID invalid or unavailable | 3, 5 |
| Error format | `def error_response(error: str, code: str, status_code: int) -> JSONResponse` from `core/errors.py` | All |

---

## Idempotency Pattern (Slices 3, 4, 5 — identical logic)

Each of these slices accepts `idempotency_key: UUID` in the request body. The check is the same every time:

```python
# 1. Check if key already exists in this slice's table
existing = await db.fetchrow(
    "SELECT * FROM <table> WHERE idempotency_key = $1",
    payload.idempotency_key,
)
# 2. If yes — return original response with status 200 (not 201)
if existing:
    return JSONResponse(status_code=200, content={...})
# 3. If no — proceed to save, then return 201
```

The only difference between slices is the table name and the response fields.

---

## Monitoring & Observability Layer (always available — no slice dependency needed)

| Service / Tool | Full signature | Purpose |
|---|---|---|
| Request logging | Middleware auto-logs every request — no manual call needed | Populates `request_logs` table (path, method, status_code, duration_ms, request_id) |
| Notification logging | `async def _log_notification(provider, channel, event_type, reference, success, error_code)` in `services/notification_service.py` | Populates `notification_logs` table — call after every Resend/Twilio attempt |
| Monitor snapshot | `async def collect_snapshot(db, window_hours) -> dict` in `services/monitor_service.py` — returns `error_rate`, `p95_latency_ms`, `notification_failures` per window | Used by `/api/internal/monitor` endpoint |
| MCP tool — request logs | `async def query_request_logs(window_hours) -> list` in `tools/db_queries.py` | Groups by path + status_code, used by monitor-db skill |
| MCP tool — notification failures | `async def query_notification_failures(window_hours) -> list` in `tools/db_queries.py` | Groups by provider + error_code, used by monitor-dependencies skill |
| MCP tool — health | `async def check_health_endpoint() -> dict` in `tools/health_check.py` | Checks production `/health` |
| MCP tool — render logs | `async def get_render_logs(lines) -> list` in `tools/render_logs.py` | Fetches Render production logs |
| MCP tool — commits | `async def get_recent_commits(count) -> list` in `tools/github_commits.py` | Fetches recent GitHub commits |
| MCP tool — provider status | `async def check_provider_status(provider) -> dict` in `tools/provider_status.py` | Checks Resend/Twilio status pages |

**Rule:** Any new slice that sends notifications must call `_log_notification` after every send attempt. Request logging is automatic via middleware.

---

## Where to Find Signatures

Each spec has a **"Signatures exposed to later slices"** block in its Dependencies section.
When the table above says "pull from Slice 1", go to `backend/specs/slice1_menu.md` → Dependencies → copy those signatures into the new spec.

**Process when starting a new spec:**
1. Check the Quick Reference table above for this slice
2. Open each listed dependency's spec file
3. Copy the "Signatures exposed" block into the new spec's Dependencies section
4. Only then start writing the spec body
