# Slice 4 — Reservations
**Status:** APPROVED 2026-04-09

## What it does
Saves a table reservation to the database and returns a reference number.
The frontend already collects all the fields — this slice wires it to a real API.

---

## Business Rules

| Rule | Detail |
|---|---|
| Party size | Must be between 1 and `max_reservation_party_size` (20 from seed data) |
| Scheduled time | Must be in the future; must be within operating hours for that day |
| Operating hours | Same config as orders — `restaurant_config.operating_hours` |
| Idempotency | Duplicate `idempotency_key` returns original response (200), no new record |
| Reference number | Same `generate_reference_number()` DB function — format `AKR-YYYYMMDD-XXXX` |
| Status | Always `confirmed` on creation |

---

## API Contract

### `POST /api/reservations`

**Request body:**
```json
{
  "idempotency_key": "uuid",
  "customer_name": "string",
  "customer_email": "string (optional)",
  "customer_phone": "string",
  "party_size": 4,
  "reserved_date": "2026-04-15",
  "reserved_time": "18:00",
  "notes": "string (optional, max 500 chars)"
}
```

**Success — 201:**
```json
{
  "reference_number": "AKR-20260415-0042",
  "status": "confirmed",
  "party_size": 4,
  "reserved_date": "2026-04-15",
  "reserved_time": "18:00"
}
```

**Error responses:**

| Code | HTTP | Meaning |
|---|---|---|
| `OUTSIDE_HOURS` | 422 | Time outside operating hours |
| `SCHEDULED_TIME_IN_PAST` | 422 | Date/time already passed |
| `PARTY_SIZE_EXCEEDED` | 422 | Exceeds `max_reservation_party_size` |
| `VALIDATION_ERROR` | 422 | Missing/invalid fields |
| `DB_UNAVAILABLE` | 503 | Unhandled exception |

---

## Test Cases

| ID | Name | Expected |
|---|---|---|
| RES-01 | Valid reservation | 201 + reference number + status confirmed |
| RES-02 | Reference number format | Matches `AKR-\d{8}-\d{4}` |
| RES-03 | Time outside operating hours | 422 `OUTSIDE_HOURS` |
| RES-04 | Date/time in the past | 422 `SCHEDULED_TIME_IN_PAST` |
| RES-05 | Party size exceeds max (21 guests) | 422 `PARTY_SIZE_EXCEEDED` |
| RES-06 | Party size of 0 | 422 `VALIDATION_ERROR` |
| RES-07 | Missing phone | 422 `VALIDATION_ERROR` |
| RES-08 | Idempotency — duplicate key returns original | 200 + same reference number, 1 DB record |
| RES-09 | Notes field stored correctly | 201, notes saved in DB |
| RES-10 | DB failure → 503 | 503 `DB_UNAVAILABLE` |

---

## Files

| File | Action |
|---|---|
| `specs/slice4_reservations.md` | This file |
| `backend/tests/test_reservations.py` | New — 10 TDD tests |
| `backend/models/reservation.py` | New — Pydantic models |
| `backend/services/reservation_service.py` | New — business logic |
| `backend/routers/reservations.py` | New — router |
| `backend/main.py` | Update — register router |
| `src/types/reservation.ts` | New — TS types |
| `src/services/reservationService.ts` | New — fetch function |
| `src/pages/ReservationPage.tsx` | Update — wire to API |

---

## Dependencies

### Reused (no changes needed)
```python
# core/timezone.py
def now_in_restaurant_time(tz: str) -> datetime

# services/config_service.py
async def get_restaurant_config(db) -> dict

# services/reference_service.py
async def generate_reference_number(db) -> str

# core/errors.py
def error_response(error: str, code: str, status_code: int) -> JSONResponse
```

### New
```python
# services/reservation_service.py
def validate_reservation_time(reserved_date: str, reserved_time: str, config: dict) -> JSONResponse | None
async def create_reservation(db, payload, config: dict) -> JSONResponse
```

---

## Frontend TypeScript Contract

```typescript
export interface ReservationCreateRequest {
  idempotency_key: string;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
  party_size: number;
  reserved_date: string;   // "YYYY-MM-DD"
  reserved_time: string;   // "HH:MM"
  notes?: string;
}

export interface ReservationCreateResponse {
  reference_number: string;
  status: string;
  party_size: number;
  reserved_date: string;
  reserved_time: string;
}
```
