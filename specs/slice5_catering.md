# Spec — Slice 5: Catering Orders
**Status: DRAFT — awaiting sign-off**
**Slice tasks:** 2.5.1 → 2.5.7
**References:** architecture.md §catering, execution-plan.md §Slice 5

---

## Requirements Coverage

| Req ID | Requirement (short) | Covered in this spec | Deferred to |
|---|---|---|---|
| CAT-01 | Customers can place catering orders without an account | ✅ POST /api/catering, no auth required | — |
| CAT-02 | Must provide: name, email, phone, event date/time, delivery address | ✅ Request shape — all fields required | — |
| CAT-03 | 48-hour advance rule, validated server-side | ✅ Business rule CAT-R01 + test CAT-03 | — |
| CAT-04 | $100 minimum order enforced | ✅ Business rule CAT-R02 + test CAT-04 | — |
| CAT-05 | Only `catering_available=true` items shown | ✅ CAT-R04 + frontend filter from menu API | — |
| CAT-06 | Select items by trays; per-tray price | ✅ Request shape + server-side pricing CAT-R05 | — |
| CAT-07 | Reference number generated and shown to customer | ✅ Response shape + success screen | — |
| CAT-08 | Customer receives confirmation email | ❌ | Slice 6 |
| CAT-09 | Owner receives email + WhatsApp notification | ❌ | Slice 6 |
| CAT-10 | Orders auto-confirmed on placement | ✅ status = "confirmed" in response | — |
| CAT-11 | Only owner can cancel (via admin panel) | ❌ | Slice 8 |
| CAT-12 | Special instructions field | ✅ `special_instructions` in request shape | — |
| CAT-13 | 40% deposit calculated and shown on success screen | ✅ `deposit_amount` in response + frontend success screen | — |

---

## What This Slice Does

Saves catering orders to the database. Enforces a 48-hour advance booking rule, a $100 minimum order, and calculates a 40% deposit amount from the database config. Frontend switches from static `menuItems` to the live menu API for catering items.

---

## Endpoint

| Field | Value |
|---|---|
| Method | `POST` |
| Path | `/api/catering` |
| Auth required | No — public |
| Rate limited | Yes (same as orders) |

---

## Request Shape

```json
{
  "idempotency_key": "uuid-string",
  "customer_name": "Priya Sharma",
  "customer_email": "priya@example.com",
  "customer_phone": "555-123-4567",
  "event_date": "2026-05-10",
  "event_time": "18:00",
  "delivery_address": "123 Main St, Chicago, IL 60601",
  "zip_code": "98004",
  "items": [
    { "item_id": "butter-chicken", "trays": 2 },
    { "item_id": "samosa", "trays": 3 }
  ],
  "special_instructions": "No nuts please"
}
```

**Field notes:**
- `customer_email` — required (not optional — catering always needs a contact email)
- `event_date` — `"YYYY-MM-DD"` string
- `event_time` — `"HH:MM"` string, 24-hour format
- `items` — at least 1 item, each with `item_id` (text slug) and `trays` (positive integer)
- `special_instructions` — optional

---

## Response Shape (success — 201 Created)

```json
{
  "reference_number": "AKR-20260510-0001",
  "status": "confirmed",
  "total_amount": 150.00,
  "deposit_amount": 60.00,
  "event_date": "2026-05-10",
  "event_time": "18:00"
}
```

**Field notes:**
- `total_amount` — calculated by backend from DB prices (never trusted from client)
- `deposit_amount` — `total_amount * catering_deposit_percent / 100` (config value, default 40%)
- `status` — always `"confirmed"` for new orders

---

## Business Rules

| Rule ID | Rule | Detail |
|---|---|---|
| CAT-R01 | 48-hour advance | `event_date + event_time` must be at least `catering_advance_hours` (48) hours from current time in restaurant timezone |
| CAT-R02 | Minimum order | `total_amount` must be >= `min_catering_order` ($100.00 from config) |
| CAT-R03 | Valid items | Each `item_id` must exist in `menu_items` with `is_available = true` |
| CAT-R04 | Catering-enabled items | Each `item_id` must have `catering_available = true` |
| CAT-R05 | Server-side pricing | Backend fetches `catering_price_per_tray` from DB — client price is never used |
| CAT-R06 | Price snapshot | `name` and `price_per_tray` are stored in `catering_order_items` at time of order |
| CAT-R06b | Zip code in delivery zone | `zip_code` must exist in `delivery_zones` table (`is_active = true`). Phase 2: upgrade to geocoding radius check. |
| CAT-R07 | Idempotency | If `idempotency_key` already exists, return HTTP 200 with original response (no duplicate insert) |
| CAT-R08 | Deposit calculation | `deposit_amount = round(total * catering_deposit_percent / 100, 2)` |

---

## Error Cases

| Scenario | HTTP | Code |
|---|---|---|
| `item_id` not found or `is_available = false` | 422 | `INVALID_MENU_ITEM` |
| `item_id` has `catering_available = false` | 422 | `ITEM_NOT_CATERING_AVAILABLE` |
| `zip_code` not in `delivery_zones` | 422 | `ZIP_NOT_COVERED` |
| `total_amount` < `min_catering_order` | 422 | `BELOW_MIN_CATERING_ORDER` |
| `event_date + event_time` < 48h from now | 422 | `LESS_THAN_48_HOURS` |
| Empty `items` list | 422 | Pydantic `min_length=1` validation |
| Missing required field | 422 | Pydantic field validation |
| DB connection failure | 503 | `DB_UNAVAILABLE` |

Error response format: `{"error": "...", "code": "..."}`

---

## Config Changes Required

`config_service.py` does not currently fetch `catering_deposit_percent`. Before the service is written, add it to the SELECT in `get_restaurant_config()`:

```python
# Add to the SELECT list in config_service.py
catering_deposit_percent
```

---

## Dependencies on Other Slices

**From Slice 1 — Menu (Read):**

```python
# services/menu_service.py
async def validate_menu_items(db, item_ids: list[str]) -> None:
    """Raises HTTP 422 INVALID_MENU_ITEM if any id is not found or is_available=false."""

# models/menu.py — MenuItem fields used:
# catering_available: bool
# catering_price_per_tray: float | None
```

**Shared services (always inject):**

```python
async def get_restaurant_config(db) -> dict
# Keys used: timezone, catering_advance_hours, min_catering_order, catering_deposit_percent

async def generate_reference_number(db) -> str
def now_in_restaurant_time(tz: str) -> datetime
def error_response(error: str, code: str, status_code: int) -> JSONResponse
```

**Idempotency pattern (same as Slices 3 and 4):**

```python
existing = await db.fetchrow(
    "SELECT reference_number, status, total::float, event_date::text, event_time FROM catering_orders WHERE idempotency_key = $1",
    payload.idempotency_key,
)
if existing:
    row = dict(existing)
    deposit_pct = config["catering_deposit_percent"]
    deposit_amount = round(row["total"] * deposit_pct / 100, 2)
    return JSONResponse(status_code=200, content={
        "reference_number": row["reference_number"],
        "status": row["status"],
        "total_amount": row["total"],
        "deposit_amount": deposit_amount,
        "event_date": row["event_date"],
        "event_time": row["event_time"],
    })
```

---

## Signatures Exposed to Later Slices

```python
# services/catering_service.py

async def create_catering_order(db, payload, config: dict) -> JSONResponse:
    """Validate and save a catering order. Returns 201 on success, 200 on duplicate, 4xx on validation failure."""

async def fetch_catering_items(db, item_ids: list[str]) -> list[dict]:
    """Returns [{item_id, name, catering_price_per_tray}] for each id.
    Raises 422 INVALID_MENU_ITEM if not found/unavailable, 422 ITEM_NOT_CATERING_AVAILABLE if catering_available=false."""
```

---

## Files to Create or Modify

| File | Action | Purpose |
|---|---|---|
| `backend/models/catering.py` | Create | `CateringItemRequest`, `CateringCreateRequest`, `CateringCreateResponse` |
| `backend/services/catering_service.py` | Create | Business logic — validate, price, save |
| `backend/services/config_service.py` | Modify | Add `catering_deposit_percent` to SELECT |
| `backend/routers/catering.py` | Create | `POST /api/catering` |
| `backend/main.py` | Modify | Register catering router |
| `backend/tests/test_catering.py` | Create | 10 tests (written first, all fail) |
| `src/types/catering.ts` | Create | TypeScript request/response types |
| `src/services/cateringService.ts` | Create | `POST /api/catering` fetch call |
| `src/pages/CateringPage.tsx` | Modify | Use menu API, add name/email/phone, call API, show reference number + deposit |

---

## Frontend Changes

**CateringPage.tsx needs:**
1. Replace `import { menuItems } from "@/data/menu"` with `useEffect` call to menu API (`getMenu()`)
2. Filter for `catering_available === true` from API response
3. Add `customer_name`, `customer_email`, `customer_phone` fields (pre-condition gap)
4. Replace local 48h check (keep it for UX) but rely on backend as source of truth
5. On submit: call `createCateringOrder()` from `cateringService.ts` instead of `setSubmitted(true)`
6. Success screen: show `reference_number` (mono font), `total_amount`, `deposit_amount`, `event_date`, `event_time`
7. Error handling: `LESS_THAN_48_HOURS`, `BELOW_MIN_CATERING_ORDER`, `INVALID_MENU_ITEM`, `ITEM_NOT_CATERING_AVAILABLE`

---

## Tests to Write (Before Any Code)

| Test ID | Test name | What it verifies |
|---|---|---|
| CAT-01 | `test_valid_catering_order_returns_201` | Valid order → 201 with `reference_number`, `status`, `total_amount`, `deposit_amount`, `event_date`, `event_time` |
| CAT-02 | `test_idempotency_returns_200` | Duplicate `idempotency_key` → 200 with same `reference_number` |
| CAT-03 | `test_event_less_than_48h_returns_422` | `event_date` < 48h from now → 422 `LESS_THAN_48_HOURS` |
| CAT-04 | `test_below_min_order_returns_422` | Single cheap item totaling < $100 → 422 `BELOW_MIN_CATERING_ORDER` |
| CAT-05 | `test_invalid_item_id_returns_422` | Non-existent `item_id` → 422 `INVALID_MENU_ITEM` |
| CAT-06 | `test_non_catering_item_returns_422` | `item_id` with `catering_available=false` → 422 `ITEM_NOT_CATERING_AVAILABLE` |
| CAT-07 | `test_empty_items_returns_422` | `items: []` → 422 (Pydantic validation) |
| CAT-08 | `test_deposit_amount_is_correct_percentage` | `deposit_amount == round(total_amount * 0.40, 2)` |
| CAT-09 | `test_order_saved_to_both_tables` | After 201, rows exist in `catering_orders` AND `catering_order_items` |
| CAT-10 | `test_missing_customer_email_returns_422` | Missing `customer_email` → 422 (required field) |

---

## TDD Sequence

```
Step 1  — Write tests/test_catering.py — all 10 tests fail
Step 2  — Update config_service.py — add catering_deposit_percent to SELECT
Step 3  — Write models/catering.py — Pydantic models
Step 4  — Write services/catering_service.py — validate + save logic
Step 5  — Write routers/catering.py — POST /api/catering
Step 6  — Register router in main.py
Step 7  — Run all tests — 10 new green + no regressions (48 existing still pass)
Step 8  — Write src/types/catering.ts
Step 9  — Write src/services/cateringService.ts
Step 10 — Update CateringPage.tsx — menu API + customer fields + success screen
Step 11 — Manual verification in browser
```

---

## Sign-off

- [ ] Vikas reviewed and approved this spec
- [ ] All 10 tests written and failing before any code written
- [ ] All 10 tests passing before moving to Slice 6
