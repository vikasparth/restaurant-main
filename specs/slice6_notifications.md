# Spec — Slice 6: Notifications
**Status: SIGNED OFF — 2026-04-12**
**Slice tasks:** 2.6.1 → 2.6.7
**References:** docs/architecture.md §notifications, execution-plan.md §Slice 6

---

## Requirements Coverage

> **Before writing this spec:** grep `docs/requirements.md` for `NOT-` and `RES-08`, `RES-09` only.

| Req ID | Requirement (short) | Covered in this spec | Deferred to |
|---|---|---|---|
| NOT-01 | Customer order confirmation email | ✅ `send_order_customer_email` | — |
| NOT-02 | Customer reservation confirmation email | ✅ `send_reservation_customer_email` | — |
| NOT-03 | Customer catering confirmation email | ✅ `send_catering_customer_email` | — |
| NOT-04 | Owner order notification (email + WhatsApp) | ✅ `send_order_owner_notifications` | — |
| NOT-05 | Owner reservation notification (email + WhatsApp) | ✅ `send_reservation_owner_notifications` | — |
| NOT-06 | Owner catering notification (email + WhatsApp) | ✅ `send_catering_owner_notifications` | — |
| NOT-07 | Customer reservation reminder email 24h before | ✅ reminder query + `send_reservation_reminder_email` | — |
| NOT-08 | Emails via Resend | ✅ `email_service.py` wraps Resend SDK | — |
| NOT-09 | WhatsApp via Twilio | ✅ `whatsapp_service.py` wraps Twilio SDK | — |
| NOT-10 | Owner WhatsApp: +1 425-439-8426 | ✅ `OWNER_WHATSAPP` env var | — |
| NOT-11 | Owner notification email: vikasparth@gmail.com | ✅ `OWNER_EMAIL` env var | — |
| RES-08 | Reminder email 24h before reservation | ✅ reminder endpoint + pg_cron | — |
| RES-09 | Cron via Supabase pg_cron, daily 9am Pacific | ✅ pg_cron SQL migration | — |

---

## What This Slice Does

Wires email and WhatsApp notifications into the three existing services (orders, reservations, catering). Notifications fire **after** the DB save — a send failure never blocks or reverses the saved record. Also adds a reservation reminder that runs daily via Supabase pg_cron.

---

## Architecture

```
order_service.py          ──► notification_service.py ──► email_service.py (Resend)
reservation_service.py    ──►                          ──► whatsapp_service.py (Twilio)
catering_service.py       ──►
```

Three new service files:

| File | Responsibility |
|---|---|
| `backend/services/email_service.py` | Send a single transactional email via Resend |
| `backend/services/whatsapp_service.py` | Send a single WhatsApp message via Twilio |
| `backend/services/notification_service.py` | Orchestrate: builds message content, calls email + WhatsApp, catches errors |

---

## New Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `RESEND_API_KEY` | Resend API key | `re_...` |
| `RESEND_FROM_EMAIL` | Verified sender address | `orders@aapkirasoi.com` |
| `OWNER_EMAIL` | Owner's notification email (NOT-11) | `vikasparth@gmail.com` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | — |
| `TWILIO_WHATSAPP_FROM` | Twilio sandbox/prod number | `whatsapp:+14155238886` |
| `OWNER_WHATSAPP` | Owner's WhatsApp number (NOT-10) | `whatsapp:+14254398426` |

All added to `.env.example` (no real values committed).

---

## Reliability Rules (REL-02, REL-03)

Notifications are wrapped in `try/except` inside `notification_service.py`. If Resend or Twilio raises, the exception is logged and execution continues. The order/reservation/catering record is **already saved** before any notification is attempted.

```python
async def notify_order(order_data: dict) -> None:
    try:
        await send_order_customer_email(order_data)
    except Exception as e:
        logger.error("Order customer email failed: %s", e)
    try:
        await send_order_owner_email(order_data)
    except Exception as e:
        logger.error("Order owner email failed: %s", e)
    try:
        await send_order_owner_whatsapp(order_data)
    except Exception as e:
        logger.error("Order WhatsApp failed: %s", e)
```

Same pattern for reservations and catering.

---

## Call Points (Modifications to Existing Services)

### `services/order_service.py`

After the `RETURNING id` insert and line items loop, add:

```python
from services.notification_service import notify_order

# After all DB writes succeed:
await notify_order({
    "reference_number": reference_number,
    "customer_name": payload.customer_name,
    "customer_email": payload.customer_email,
    "order_type": payload.order_type,
    "scheduled_time": payload.scheduled_time,
    "total_amount": total,
    "delivery_fee": delivery_fee,
    "line_items": line_items,
    "special_instructions": payload.special_instructions,
})
```

### `services/reservation_service.py`

After INSERT:

```python
from services.notification_service import notify_reservation

await notify_reservation({
    "reference_number": reference_number,
    "customer_name": payload.customer_name,
    "customer_email": payload.customer_email,
    "customer_phone": payload.customer_phone,
    "reservation_date": payload.reservation_date,
    "reservation_time": payload.reservation_time,
    "party_size": payload.party_size,
    "special_instructions": payload.special_instructions,
})
```

### `services/catering_service.py`

After the catering_order_items loop:

```python
from services.notification_service import notify_catering

await notify_catering({
    "reference_number": reference_number,
    "customer_name": payload.customer_name,
    "customer_email": payload.customer_email,
    "customer_phone": payload.customer_phone,
    "event_date": payload.event_date,
    "event_time": payload.event_time,
    "delivery_address": payload.delivery_address,
    "total_amount": total,
    "deposit_amount": deposit_amount,
    "line_items": line_items,
    "special_instructions": payload.special_instructions,
})
```

---

## Email Content

### Customer — Order Confirmation (NOT-01)
**Subject:** `Order Confirmed — AKR-YYYYMMDD-XXXX`

Body includes:
- Reference number
- Order type (Pickup / Delivery)
- Scheduled time
- Line items with quantities and prices
- Subtotal, delivery fee (if delivery), grand total
- Special instructions (if any)

### Customer — Reservation Confirmation (NOT-02)
**Subject:** `Reservation Confirmed — AKR-YYYYMMDD-XXXX`

Body includes: date, time, party size, reference number, special instructions (if any)

### Customer — Catering Confirmation (NOT-03)
**Subject:** `Catering Order Confirmed — AKR-YYYYMMDD-XXXX`

Body includes:
- Reference number
- Event date and time
- Delivery address
- Line items (tray counts and prices)
- Total amount
- Deposit amount + message: *"A deposit of $X is required. Our team will contact you within 24 hours to arrange payment."*
- Special instructions (if any)

### Customer — Reservation Reminder (NOT-07)
**Subject:** `Reminder: Your reservation tomorrow at HH:MM`

Body includes: date, time, party size, reference number, restaurant address

### Owner — All notifications (NOT-04, NOT-05, NOT-06)
Plain-text emails and WhatsApp messages with the same data as the customer emails, plus customer phone number.

---

## WhatsApp Message Content (Twilio)

Single plain-text message per event. Example for order:

```
New Order — AKR-20260510-0001
Customer: Priya Sharma
Phone: 555-123-4567
Type: Delivery
Time: 2026-05-10 18:00
Items: Butter Chicken x2, Samosa x3
Total: $120.00
Address: 123 Main St, Bellevue WA 98004
```

Same format adapted for reservations and catering.

---

## Reservation Reminder Endpoint + pg_cron (RES-08, RES-09)

### New endpoint

```
POST /api/internal/send-reminders
Auth: internal shared secret header (X-Internal-Token)
```

This endpoint:
1. Queries `reservations` for rows where `reservation_date = tomorrow` AND `status = 'confirmed'` AND `customer_email IS NOT NULL`
2. For each row, calls `send_reservation_reminder_email()`
3. Returns `{"sent": N}`

pg_cron fires this endpoint daily at 9am Pacific by calling `net.http_post()` (Supabase `pg_net` extension).

### New migration: `20260412000002_add_reminder_cron.sql`

```sql
-- Requires pg_cron + pg_net extensions enabled in Supabase dashboard
SELECT cron.schedule(
  'send-reservation-reminders',
  '0 9 * * *',   -- 9am UTC (adjust for Pacific: 0 17 * * * for PDT, 0 16 * * * for PST)
  $$
    SELECT net.http_post(
      url := current_setting('app.api_base_url') || '/api/internal/send-reminders',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'X-Internal-Token', current_setting('app.internal_token')
      ),
      body := '{}'::jsonb
    )
  $$
);
```

**Note:** `app.api_base_url` and `app.internal_token` are set as Supabase config vars in the dashboard.

New env var: `INTERNAL_TOKEN` — shared secret the endpoint checks.

---

## Error Cases

| Scenario | Behavior |
|---|---|
| Resend API error | Log error, return original success response |
| Twilio API error | Log error, return original success response |
| Missing `customer_email` on reservation | Skip customer email (email is optional for reservations) |
| Reminder endpoint called without valid token | 401 Unauthorized |
| Reminder endpoint: no reservations tomorrow | 200 `{"sent": 0}` |

---

## Files to Create or Modify

| File | Action | Purpose |
|---|---|---|
| `backend/services/email_service.py` | Create | Resend SDK wrapper |
| `backend/services/whatsapp_service.py` | Create | Twilio SDK wrapper |
| `backend/services/notification_service.py` | Create | Orchestrate per event type |
| `backend/routers/internal.py` | Create | `POST /api/internal/send-reminders` |
| `backend/main.py` | Modify | Register internal router |
| `backend/services/order_service.py` | Modify | Call `notify_order` after save |
| `backend/services/reservation_service.py` | Modify | Call `notify_reservation` after save |
| `backend/services/catering_service.py` | Modify | Call `notify_catering` after save |
| `backend/.env.example` | Modify | Add 7 new env vars |
| `supabase/migrations/20260412000002_add_reminder_cron.sql` | Create | pg_cron job |
| `backend/tests/test_notifications.py` | Create | 12 tests |

---

## Tests to Write (Before Any Code)

| Test ID | Test name | What it verifies |
|---|---|---|
| NOT-01 | `test_order_triggers_customer_email` | After valid order POST → customer email send called with correct data |
| NOT-02 | `test_reservation_triggers_customer_email` | After valid reservation POST → customer email called |
| NOT-03 | `test_catering_triggers_customer_email` | After valid catering POST → customer email called |
| NOT-04 | `test_order_triggers_owner_email_and_whatsapp` | After valid order POST → owner email AND WhatsApp called |
| NOT-05 | `test_reservation_triggers_owner_notifications` | After valid reservation POST → owner email AND WhatsApp called |
| NOT-06 | `test_catering_triggers_owner_notifications` | After valid catering POST → owner email AND WhatsApp called |
| NOT-07 | `test_email_failure_does_not_block_order` | Resend raises → order still returns 201 |
| NOT-08 | `test_whatsapp_failure_does_not_block_order` | Twilio raises → order still returns 201 |
| NOT-09 | `test_reminder_endpoint_sends_tomorrows_reservations` | Reminder endpoint → correct reservations queried and emails sent |
| NOT-10 | `test_reminder_endpoint_rejects_missing_token` | No `X-Internal-Token` → 401 |
| NOT-11 | `test_reminder_skips_reservation_without_email` | Reservation with `customer_email = null` → email not called |
| NOT-12 | `test_reservation_without_email_skips_customer_email` | Optional email on reservation → no crash, owner still notified |

**Mocking strategy:** Use `unittest.mock.patch` to mock `email_service.send_email` and `whatsapp_service.send_whatsapp`. Never mock internal notification logic — only the outbound SDK call.

---

## Dependencies Pulled from Prior Slices

### From Slice 3 (Orders)
```python
# services/order_service.py — add notify_order call after this block:
# INSERT INTO order_items ... (the items loop at the bottom of create_order)
```

### From Slice 4 (Reservations)
```python
# services/reservation_service.py — add notify_reservation call after INSERT RETURNING id
```

### From Slice 5 (Catering)
```python
# services/catering_service.py — add notify_catering call after catering_order_items loop
# line_items: list[dict] already built — [{item_id, name, price_per_tray, trays}]
```

---

## Signatures Exposed to Later Slices

```python
# services/notification_service.py

async def notify_order(order_data: dict) -> None:
    """Fire customer + owner email and owner WhatsApp for a new order. Never raises."""

async def notify_reservation(reservation_data: dict) -> None:
    """Fire customer (if email present) + owner email and owner WhatsApp. Never raises."""

async def notify_catering(catering_data: dict) -> None:
    """Fire customer + owner email and owner WhatsApp for a catering order. Never raises."""

async def send_reservation_reminders(db) -> int:
    """Query tomorrow's confirmed reservations, send reminders. Returns count sent."""
```

---

## TDD Sequence

```
Step 1  — Write tests/test_notifications.py — all 12 tests fail
Step 2  — Create services/email_service.py — Resend wrapper
Step 3  — Create services/whatsapp_service.py — Twilio wrapper
Step 4  — Create services/notification_service.py — orchestrator
Step 5  — Modify order_service.py — add notify_order call
Step 6  — Modify reservation_service.py — add notify_reservation call
Step 7  — Modify catering_service.py — add notify_catering call
Step 8  — Create routers/internal.py — reminder endpoint
Step 9  — Register internal router in main.py
Step 10 — Run full test suite — 12 new green + no regressions (59 existing still pass)
Step 11 — Add env vars to .env.example
Step 12 — Write migration 20260412000002_add_reminder_cron.sql
Step 13 — Manual verification: place order, check email + WhatsApp received
```

---

## Sign-off

- [x] Vikas reviewed and approved this spec
- [x] All 12 tests written and failing before any code written
- [x] All 12 tests passing before moving to Slice 7
