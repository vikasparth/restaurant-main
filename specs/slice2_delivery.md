# Spec — Slice 2: Delivery Validation
**Status: DRAFT — Awaiting sign-off by Vikas**
**Slice tasks:** 2.2.1 → 2.2.7
**References:** docs/architecture.md §delivery_zones table, §rate limiting

---

## What This Slice Does

When a customer selects delivery on the order page and enters their zip code, the frontend
asks the backend: "do you deliver here?". The backend checks the `delivery_zones` table
and replies yes or no. If no, the customer sees a friendly message before they waste time
filling out the order form.

---

## Endpoint

| Field | Value |
|---|---|
| Method | `POST` |
| Path | `/api/delivery/validate` |
| Auth required | No — public |
| Rate limited | Yes — public POST, abuse risk |

---

## Request Shape

```json
{ "zip_code": "98004" }
```

- `zip_code` — required string, must not be empty

---

## Response Shape (success)

HTTP 200 in all non-error cases.

**Zip is covered:**
```json
{ "is_covered": true, "city": "Bellevue" }
```

**Zip is not covered:**
```json
{ "is_covered": false, "city": null }
```

**Why always 200?** A zip not being in our delivery zone is a normal business outcome,
not an error. We only use 4xx/5xx for genuine failures.

---

## Business Rules

| Rule | Detail |
|---|---|
| Zip must match exactly | Case-insensitive, trimmed of whitespace before lookup |
| Only active zones count | Query filters `is_active = true` |
| Location scoped | Queries only zones for `DEFAULT_LOCATION_ID` from config |
| Not found = not covered | If zip is not in the table, return `is_covered: false` — not an error |

---

## Error Cases

| Scenario | HTTP Status | Code |
|---|---|---|
| Missing or empty zip_code | 422 | `VALIDATION_ERROR` |
| Database connection failure | 503 | `DB_UNAVAILABLE` |

---

## Shared Services Used

| Service | File | Why |
|---|---|---|
| DB connection pool | `core/database.py` | All DB queries go through the shared pool |
| Config (location_id) | `core/config.py` | Reads `DEFAULT_LOCATION_ID` from env |
| Rate limiter | `core/rate_limit.py` | Applied to all public POST endpoints |

---

## Dependencies on Other Slices

| Dependency | Detail |
|---|---|
| None | Slice 2 is independent — no other slice is required first |

**Signatures exposed to later slices:**

```python
# services/delivery_service.py

async def validate_zip(db, zip_code: str) -> dict | None:
    """
    Returns {"zip_code": str, "city": str} if zip is in an active delivery zone
    for the configured location, or None if not covered.
    """
```

**Consumed by:**
- Slice 3 (Orders): calls `validate_zip()` to confirm delivery orders are within range before saving

---

## What This Does NOT Include

- Delivery fee calculation (Phase 2)
- Estimated delivery time (Phase 2)
- Adding/removing delivery zones (Slice 7 — Admin)

---

## Files to Create

| File | Purpose |
|---|---|
| `backend/models/delivery.py` | Pydantic models: `DeliveryValidateRequest`, `DeliveryValidateResponse` |
| `backend/services/delivery_service.py` | Business logic: query `delivery_zones` table |
| `backend/routers/delivery.py` | HTTP layer: `POST /api/delivery/validate` |
| `backend/tests/test_delivery.py` | pytest tests (written before the code) |
| `src/services/deliveryService.ts` | Frontend: call the validate endpoint |
| `src/types/delivery.ts` | Frontend: TypeScript types for request/response |

---

## Frontend TypeScript Contract

```typescript
// src/types/delivery.ts

export interface DeliveryValidateRequest {
  zip_code: string;
}

export interface DeliveryValidateResponse {
  is_covered: boolean;
  city: string | null;
}
```

---

## Tests to Write (Before Any Code)

| Test ID | Test name | What it verifies |
|---|---|---|
| DEL-01 | `test_valid_zip_returns_covered` | A seeded zip returns `is_covered: true` with correct city |
| DEL-02 | `test_invalid_zip_returns_not_covered` | Unknown zip returns `is_covered: false`, `city: null` |
| DEL-03 | `test_empty_zip_returns_422` | Empty string zip returns HTTP 422 |
| DEL-04 | `test_missing_zip_returns_422` | Request body without `zip_code` field returns HTTP 422 |
| DEL-05 | `test_zip_is_trimmed` | Zip with leading/trailing spaces (e.g. `" 98004 "`) still matches |
| DEL-06 | `test_inactive_zone_not_covered` | Zip that exists but `is_active = false` returns `is_covered: false` |
| DEL-07 | `test_db_failure_returns_503` | Simulated DB failure returns HTTP 503 with `code: DB_UNAVAILABLE` |

---

## TDD Sequence (How We Will Build This)

```
Step 1  — Write tests/test_delivery.py — all 7 tests fail
Step 2  — Write models/delivery.py — request + response models
Step 3  — Write services/delivery_service.py — validate_zip() DB query
Step 4  — Write routers/delivery.py — POST /api/delivery/validate
Step 5  — Register router in main.py
Step 6  — Run tests — all 7 should go green
Step 7  — Write src/types/delivery.ts
Step 8  — Write src/services/deliveryService.ts
Step 9  — Update OrderPage.tsx to validate zip before showing delivery form
Step 10 — Manual verification in browser
```

---

## Sign-off

- [x] Vikas reviewed and approved this spec ✅ 2026-04-07
- [ ] All 7 tests written and failing before any code written
- [ ] All 7 tests passing before moving to Slice 3
