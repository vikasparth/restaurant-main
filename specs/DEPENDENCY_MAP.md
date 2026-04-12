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

## Where to Find Signatures

Each spec has a **"Signatures exposed to later slices"** block in its Dependencies section.
When the table above says "pull from Slice 1", go to `specs/slice1_menu.md` → Dependencies → copy those signatures into the new spec.

**Process when starting a new spec:**
1. Check the Quick Reference table above for this slice
2. Open each listed dependency's spec file
3. Copy the "Signatures exposed" block into the new spec's Dependencies section
4. Only then start writing the spec body
