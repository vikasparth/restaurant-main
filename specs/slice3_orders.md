# Spec — Slice 3: Orders
**Status: APPROVED — Signed off by Vikas, 2026-04-09**
**Slice tasks:** 2.3.1 → 2.3.9
**References:** architecture.md §orders table, §order_items table, §restaurant_config, §Shared Contracts, §Idempotency Pattern, §Business Rules

---

## What This Slice Does

When a customer fills out the order form (pickup or delivery), the frontend sends all their details to the backend. The backend validates the order (operating hours, delivery zip, minimum order value, menu items), saves it, and returns a reference number that shows on the success screen. This is the core revenue-generating flow of the restaurant.

---

## Endpoint

| Field | Value |
|---|---|
| Method | `POST` |
| Path | `/api/orders` |
| Auth required | No — public (guest checkout) |
| Rate limited | Yes — public POST, abuse risk |

---

## Request Shape

```json
{
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "customer_name": "Priya Sharma",
  "customer_email": "priya@example.com",
  "customer_phone": "4255550123",
  "order_type": "delivery",
  "scheduled_date": "2026-04-09",
  "scheduled_time": "18:30",
  "items": [
    { "menu_item_id": "samosa", "quantity": 2 },
    { "menu_item_id": "butter-chicken", "quantity": 1 }
  ],
  "delivery_address": "123 Main St",
  "delivery_zip": "98004",
  "special_instructions": "Extra napkins please"
}
```

### Field rules

| Field | Type | Required | Validation |
|---|---|---|---|
| `idempotency_key` | UUID string | Yes | Must be a valid UUID v4 |
| `customer_name` | string | Yes | Non-empty |
| `customer_email` | string | Yes | Valid email format |
| `customer_phone` | string | Yes | Non-empty |
| `order_type` | string | Yes | Must be `"pickup"` or `"delivery"` |
| `scheduled_date` | string | Yes | ISO date format `YYYY-MM-DD` |
| `scheduled_time` | string | Yes | `HH:MM` 24-hour format |
| `items` | array | Yes | At least 1 item |
| `items[].menu_item_id` | string | Yes | Non-empty |
| `items[].quantity` | integer | Yes | ≥ 1 |
| `delivery_address` | string | Required if `order_type = "delivery"` | Non-empty |
| `delivery_zip` | string | Required if `order_type = "delivery"` | Non-empty |
| `special_instructions` | string | No | Optional, max 500 chars |

---

## Response Shape (success)

HTTP 201. Payload returned directly — no envelope wrapper.

```json
{
  "reference_number": "AKR-20260409-0042",
  "status": "confirmed",
  "order_type": "delivery",
  "scheduled_date": "2026-04-09",
  "scheduled_time": "18:30",
  "subtotal": 17.97,
  "delivery_fee": 4.99,
  "total": 22.96
}
```

**Why 201?** A new resource (the order) has been created. The reference number is shown on the frontend success screen.

**Idempotent repeat:** If `idempotency_key` already exists in the DB, return HTTP 200 with the original saved response — do not create a new order.

---

## Business Rules

| Rule | Detail | Config source |
|---|---|---|
| Scheduled time must be during operating hours | `scheduled_date` + `scheduled_time` validated against `operating_hours` JSON in `restaurant_config` | `restaurant_config.operating_hours` |
| Scheduled time must be in the future | After converting to restaurant timezone (Pacific) | `restaurant_config.timezone` |
| Restaurant not closed on that day | `scheduled_date` must not be in `closed_days` array | `restaurant_config.closed_days` |
| Delivery zip must be in an active zone | Calls `validate_zip()` from Slice 2 | `delivery_zones` table |
| Minimum delivery order | Subtotal must be ≥ `min_delivery_order` (default $25) | `restaurant_config.min_delivery_order` |
| Delivery fee applied | Added to subtotal for delivery orders | `restaurant_config.delivery_fee` |
| Pickup orders have no delivery fee | `delivery_fee = 0` | — |
| Menu items must be valid and available | Calls `validate_menu_items()` from Slice 1 | `menu_items` table |
| Prices snapshotted at order time | `order_items.price` is read from `menu_items.price` at the moment of submission; future price changes do not affect past orders | `menu_items.price` |
| Idempotency | `idempotency_key` (UUID) must be unique in `orders` table. Duplicate key → return original response, no new record | `orders.idempotency_key` |

---

## Error Cases

| Scenario | HTTP Status | Code |
|---|---|---|
| Missing required field or wrong type | 422 | `VALIDATION_ERROR` |
| Invalid `order_type` value | 422 | `VALIDATION_ERROR` |
| `delivery_address` / `delivery_zip` missing for delivery order | 422 | `VALIDATION_ERROR` |
| Any `menu_item_id` not found or `is_available = false` | 422 | `INVALID_MENU_ITEM` |
| Delivery zip not in an active delivery zone | 422 | `ZIP_NOT_COVERED` |
| Subtotal below minimum delivery order amount | 422 | `BELOW_MIN_ORDER` |
| Scheduled time outside operating hours | 422 | `OUTSIDE_HOURS` |
| Scheduled time is in the past | 422 | `SCHEDULED_TIME_IN_PAST` |
| Scheduled date is a closed day | 422 | `RESTAURANT_CLOSED` |
| Database connection failure | 503 | `DB_UNAVAILABLE` |

---

## Shared Services Used

| Service | File | Why |
|---|---|---|
| DB connection pool | `core/database.py` | All DB queries go through the shared pool |
| Config (location_id) | `core/config.py` | Reads `DEFAULT_LOCATION_ID` from env |
| Restaurant config | `services/config_service.get_restaurant_config(db)` | Operating hours, delivery fee, min order, timezone, closed days |
| Reference number | `services/reference_service.generate_reference_number(db)` | Generates `AKR-YYYYMMDD-XXXX` format |
| Timezone | `core/timezone.to_restaurant_time(dt, tz)` | Validates scheduled time in restaurant's local time |
| Menu validation | `services/menu_service.validate_menu_items(db, ids)` | Validates and fetches prices for items in the order |
| Delivery validation | `services/delivery_service.validate_zip(db, zip_code)` | Confirms zip is in an active delivery zone |
| Rate limiter | `core/rate_limit.py` | Applied to all public POST endpoints |
| Error format | `core/errors.py` | Consistent error responses |

---

## Dependencies on Other Slices

Slice 3 depends on both Slice 1 and Slice 2. Pull exact signatures from their specs.

| Slice | File | Why needed |
|---|---|---|
| Slice 1 (Menu) | `services/menu_service.py` | Validate items exist and are available; read current prices for snapshot |
| Slice 2 (Delivery) | `services/delivery_service.py` | Confirm zip code is in an active delivery zone |

```python
# From specs/slice1_menu.md — "Signatures exposed to later slices"
# services/menu_service.py

async def validate_menu_items(db, item_ids: list[str]) -> None:
    """Raises HTTP 422 INVALID_MENU_ITEM if any id is not found or is_available=false."""

# models/menu.py — MenuItem shape
class MenuItem(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    is_vegetarian: bool
    is_available: bool
    catering_available: bool
    catering_price_per_tray: float | None
    allergens: list[str]
    display_order: int
```

```python
# From specs/slice2_delivery.md — "Signatures exposed to later slices"
# services/delivery_service.py

async def validate_zip(db, zip_code: str) -> dict | None:
    """
    Returns {"zip_code": str, "city": str} if zip is in an active delivery zone
    for the configured location, or None if not covered.
    """
```

**Signatures exposed by THIS slice to later slices:**

```python
# services/order_service.py

async def create_order(db, payload: OrderCreateRequest, config: RestaurantConfig) -> dict:
    """
    Validates and saves a new order (or returns existing if idempotency_key matches).
    Returns {"reference_number": str, "status": str, "order_type": str,
             "scheduled_date": str, "scheduled_time": str,
             "subtotal": float, "delivery_fee": float, "total": float}.
    Raises HTTP 422 for any business rule violation.
    """
```

**Consumed by:**
- Slice 6 (Notifications): hooks into order creation to send confirmation email + WhatsApp to owner

---

## What This Does NOT Include

- Payment processing (Phase 2 — Stripe)
- Delivery fee calculation beyond flat fee from config (Phase 2)
- Estimated delivery time (Phase 2)
- Order status updates (Slice 8 — Admin endpoints)
- Listing orders (Slice 8 — Admin endpoints)
- Customer cancellations (Phase 2)
- Email/WhatsApp notifications (Slice 6 — wired after this slice works)

---

## Test Data Setup

Tests rely on seed data from `20260406000002_seed_data.sql`:
- At least 2 available menu items with known prices (e.g. `samosa` at $5.99, `butter-chicken` at $14.99)
- At least 1 menu item with `is_available = false` (needed for ORD-08)
- At least 1 active delivery zip code in `delivery_zones` (e.g. `98004`)
- `restaurant_config` seeded with: timezone `America/Los_Angeles`, operating hours Mon–Sun 11:00–21:00, `min_delivery_order = 25.00`, `delivery_fee = 4.99`

`conftest.py` handles DB setup/teardown between tests. Tests that check scheduled time must use a future date+time relative to test execution.

---

## Files to Create

| File | Purpose |
|---|---|
| `backend/models/order.py` | Pydantic models: `OrderCreateRequest`, `OrderItemRequest`, `OrderCreateResponse` |
| `backend/services/order_service.py` | Business logic: validate hours, zip, min order, items; save order + items; return response |
| `backend/routers/orders.py` | HTTP layer: `POST /api/orders` |
| `backend/tests/test_orders.py` | pytest tests (written before any code) |
| `src/types/order.ts` | Frontend TypeScript types |
| `src/services/orderService.ts` | Frontend fetch function |

---

## Frontend TypeScript Contract

```typescript
// src/types/order.ts

export interface OrderItem {
  menu_item_id: string;
  quantity: number;
}

export interface OrderCreateRequest {
  idempotency_key: string;          // UUID v4 generated by frontend before submission
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  order_type: 'pickup' | 'delivery';
  scheduled_date: string;           // YYYY-MM-DD
  scheduled_time: string;           // HH:MM (24h)
  items: OrderItem[];
  delivery_address?: string;
  delivery_zip?: string;
  special_instructions?: string;
}

export interface OrderCreateResponse {
  reference_number: string;
  status: string;
  order_type: string;
  scheduled_date: string;
  scheduled_time: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
}
```

---

## Tests to Write (Before Any Code)

| Test ID | Test name | What it verifies |
|---|---|---|
| ORD-01 | `test_valid_pickup_order_returns_201` | Valid pickup order saves and returns reference number + status |
| ORD-02 | `test_valid_delivery_order_returns_201` | Valid delivery order saves with delivery fee applied |
| ORD-03 | `test_pickup_order_has_zero_delivery_fee` | Pickup order returns `delivery_fee: 0` |
| ORD-04 | `test_price_snapshot_on_order_items` | `order_items.price` matches `menu_items.price` at time of order |
| ORD-05 | `test_reference_number_format` | Reference number matches `AKR-YYYYMMDD-XXXX` pattern |
| ORD-06 | `test_scheduled_time_outside_hours_returns_422` | Time outside operating hours returns 422 `OUTSIDE_HOURS` |
| ORD-07 | `test_scheduled_time_in_past_returns_422` | Past scheduled time returns 422 `SCHEDULED_TIME_IN_PAST` |
| ORD-08 | `test_unavailable_menu_item_returns_422` | Item with `is_available=false` returns 422 `INVALID_MENU_ITEM` |
| ORD-09 | `test_unknown_menu_item_returns_422` | Non-existent `menu_item_id` returns 422 `INVALID_MENU_ITEM` |
| ORD-10 | `test_delivery_zip_not_covered_returns_422` | Unrecognised zip returns 422 `ZIP_NOT_COVERED` |
| ORD-11 | `test_delivery_below_min_order_returns_422` | Subtotal below `min_delivery_order` returns 422 `BELOW_MIN_ORDER` |
| ORD-12 | `test_delivery_missing_zip_returns_422` | Delivery order without `delivery_zip` returns 422 `VALIDATION_ERROR` |
| ORD-13 | `test_delivery_missing_address_returns_422` | Delivery order without `delivery_address` returns 422 `VALIDATION_ERROR` |
| ORD-14 | `test_missing_items_returns_422` | Empty `items` array returns 422 `VALIDATION_ERROR` |
| ORD-15 | `test_invalid_order_type_returns_422` | `order_type: "dine_in"` returns 422 `VALIDATION_ERROR` |
| ORD-16 | `test_invalid_quantity_returns_422` | `quantity: 0` returns 422 `VALIDATION_ERROR` |
| ORD-17 | `test_idempotency_duplicate_key_returns_original` | Sending same `idempotency_key` twice returns HTTP 200 with original response, no duplicate record |
| ORD-18 | `test_db_failure_returns_503` | Simulated DB failure returns 503 `DB_UNAVAILABLE` |

---

## TDD Sequence (How We Will Build This)

```
Step 1  — Write backend/tests/test_orders.py — all 18 tests fail (no code yet)
Step 2  — Write backend/models/order.py — request + response Pydantic models
Step 3  — Write backend/services/order_service.py:
            a. validate_scheduled_time() — hours + past check
            b. calculate_totals() — subtotal, delivery_fee, total
            c. create_order() — full orchestration (validate → save → return)
Step 4  — Write backend/routers/orders.py — POST /api/orders
Step 5  — Register router in main.py
Step 6  — Run tests — all 18 should go green
Step 7  — Write src/types/order.ts
Step 8  — Write src/services/orderService.ts
Step 9  — Update OrderPage.tsx: add name/email/phone fields, generate idempotency_key, show reference number on success
Step 10 — Manual verification in browser
```

---

## Sign-off

- [x] Vikas reviewed and approved this spec ✅ 2026-04-09
- [ ] All 18 tests written and failing before any code written
- [ ] All 18 tests passing before moving to Slice 4
- [ ] Full test suite run (menu + delivery + orders) — all passing
