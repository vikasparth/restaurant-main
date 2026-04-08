# Architecture — Aap ki Rasoi Backend
**Status: APPROVED — Signed off by Vikas, 2026-04-06**
**Last updated: 2026-04-06**
**Reference:** See `requirements.md` for full functional requirements. See `execution-plan.md` for build order.

---

## 1. Project Overview

**Business:** Aap ki Rasoi — Indian restaurant, USA (Pacific Time)
**Goal:** Add a real backend to the existing React frontend so orders, reservations, and catering requests are saved, notifications are sent, and the owner can manage the business.

---

## 2. Agreed Constraints

| Constraint | Decision |
|---|---|
| Budget | ~$0 during development and early production. Upgrade Render to $7/mo before high-traffic go-live |
| Hosting expertise | No DevOps knowledge required |
| Language | Python (owner is learning Python through this project) |
| Country | USA |
| Payment | Stripe — Phase 2 only |
| Admin UI | Owner builds in Lovable (Phase 2) — backend API built and tested in Phase 1 |
| Customer accounts | Guest checkout — no account required to place orders |
| Staff logins | Owner only for now — staff logins considered for Phase 2 |
| Multiple locations | Schema designed for multi-location from day one |

---

## 3. Technology Stack

| Layer | Technology | Why | Monthly Cost |
|---|---|---|---|
| **Frontend** | React + Vite + TypeScript (existing) | Already built | $0 (Vercel free) |
| **Backend API** | Python + FastAPI | Modern, beginner-friendly Python framework | $0 (Render free tier) |
| **Database** | Supabase (PostgreSQL) | Managed Postgres, free tier, built-in auth | $0 free tier |
| **DB connection** | asyncpg (direct Postgres) | Better performance than Supabase client; no PostgREST intermediary | $0 |
| **Auth** (admin) | Supabase Auth + JWT verification | Built-in auth, verify JWT in FastAPI middleware | $0 |
| **Email** | Resend | Simple API, 3,000 free emails/month | $0 |
| **WhatsApp** | Twilio WhatsApp API | USA-ready, reliable, pay-per-message | ~$0.005/msg |
| **Reservation reminder** | cron-job.org | Free external cron — pings `/api/reservations/send-reminders` daily. Reliable regardless of Render sleep | $0 |
| **Rate limiting** | slowapi (FastAPI middleware) | Protects public POST endpoints from bots/spam | $0 |
| **Backend hosting** | Render.com (free tier) | Auto-deploy from GitHub, no DevOps needed. Upgrade to $7/mo before go-live | $0 dev / $7 prod |
| **Frontend hosting** | Vercel | Free tier, perfect for Vite/React | $0 |
| **Canary monitoring** | GitHub Actions (scheduled) + UptimeRobot | UptimeRobot pings `/health` every 5 min (unlimited, free); GitHub Actions runs deeper canary tests every 50 min (~864 min/month, well within 2,000 free tier limit); both alert owner email on failure | $0 |
| **Estimated total** | | | **~$0 dev, ~$7 prod** |

> **What Render does:** Render hosts your FastAPI Python backend — the server that receives orders, validates zip codes, talks to Supabase, and sends notifications. Think of it as "the computer in the cloud" running your Python code.

> **Render free tier note:** Server sleeps after 15 minutes of inactivity. First request after idle takes ~3 seconds. Use free tier during development only. Upgrade to Render Starter ($7/mo) before going live — add to pre-launch checklist.

> **Email domain note:** Resend sandbox (no custom domain) used during development. A custom domain (~$10–15/year one-time) is required before go-live to prevent confirmation emails landing in spam. Pre-launch requirement, not a blocker for building.

---

## 4. System Architecture Diagram

```
Customer Browser
      │
      │  HTTPS
      ▼
┌─────────────────────┐
│   React Frontend    │  ← Vercel (free)
│  (Vite + TypeScript)│
└──────────┬──────────┘
           │ REST API calls (HTTPS)
           ▼
┌─────────────────────┐
│   FastAPI Backend   │  ← Render.com
│     (Python)        │
│                     │
│  /health            │
│  /api/menu          │
│  /api/orders        │
│  /api/reservations  │
│  /api/catering      │
│  /api/delivery/     │
│    validate         │
│  /api/admin/*       │  ← JWT protected
└──────┬──────┬───────┘
       │      │
       │      │ Notifications
       │      ├──────────────► Resend (Email)
       │      └──────────────► Twilio (WhatsApp)
       │
       │ Direct SQL (asyncpg)
       ▼
┌─────────────────────┐
┌─────────────────────┐
│  Supabase Postgres  │  ← Supabase (free)
│  (Database + Auth)  │
└─────────────────────┘
       ▲
       │ Daily cron ping
cron-job.org ──────────► /api/reservations/send-reminders
```

---

## 5. Backend Folder Structure

```
restaurant_main_project/
│
├── backend/
│   ├── main.py                     # FastAPI app entry point, CORS, router registration
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variable template (no secrets)
│   │
│   ├── core/
│   │   ├── config.py               # App settings — reads all .env variables including DEFAULT_LOCATION_ID
│   │   ├── database.py             # asyncpg direct Postgres connection pool
│   │   ├── security.py             # Supabase JWT verification for admin routes
│   │   ├── errors.py               # Global error response format (set up in Stage 1)
│   │   ├── rate_limit.py           # slowapi rate limiter setup
│   │   ├── logging.py              # Structured logging — JSON in production, readable in dev; never logs PII
│   │   └── timezone.py             # Timezone utility — converts datetimes to restaurant local time (Pacific)
│   │
│   ├── routers/                    # HTTP layer only — no business logic here
│   │   ├── orders.py
│   │   ├── reservations.py
│   │   ├── catering.py
│   │   ├── menu.py
│   │   ├── delivery.py
│   │   └── admin.py                # Admin-only routes (analytics, config, status updates)
│   │
│   ├── services/                   # All business logic lives here
│   │   ├── menu_service.py         # Read + CRUD for menu items; exposes validate_menu_items() for orders/catering
│   │   ├── order_service.py        # Validate hours + scheduled time, save, notify
│   │   ├── reservation_service.py  # Save, notify, reminder logic
│   │   ├── catering_service.py     # 48h rule, $100 min, save, notify
│   │   ├── delivery_service.py     # Zip code validation against delivery_zones table
│   │   ├── config_service.py       # Shared: fetch restaurant_config for a location — used by orders, reservations, catering, admin
│   │   ├── reference_service.py    # Shared: generate AKR-YYYYMMDD-XXXX reference numbers — used by orders, reservations, catering
│   │   ├── analytics_service.py    # Monthly sales, pickup vs delivery, top items
│   │   ├── email_service.py        # Resend wrapper + email templates
│   │   └── whatsapp_service.py     # Twilio WhatsApp wrapper
│   │
│   ├── models/                     # Pydantic request/response models
│   │   ├── order.py
│   │   ├── reservation.py
│   │   ├── catering.py
│   │   ├── menu.py
│   │   ├── delivery.py
│   │   └── analytics.py
│   │
│   └── tests/
│       ├── conftest.py             # pytest config — DB setup/teardown, shared fixtures, API_BASE_URL env var
│       ├── test_menu.py
│       ├── test_delivery.py
│       ├── test_orders.py
│       ├── test_reservations.py
│       ├── test_catering.py
│       ├── test_auth.py            # JWT valid/invalid/expired/tampered scenarios
│       ├── test_admin_config.py    # GET + PUT config; auth enforcement
│       ├── test_analytics.py       # Analytics response shape and values; auth enforcement
│       └── canary/                 # Run against live URL — same tests, different base URL
│           ├── test_health.py      # GET /health → 200, {"status": "ok"}
│           ├── test_menu_live.py   # GET /api/menu → 200, non-empty
│           └── test_delivery_live.py  # POST /api/delivery/validate with known valid zip
│
├── src/                            # React frontend
│   ├── services/                   # Frontend API call layer (TypeScript)
│   │   ├── orderService.ts
│   │   ├── reservationService.ts
│   │   ├── cateringService.ts
│   │   ├── menuService.ts
│   │   └── deliveryService.ts
│   └── types/
│       ├── order.ts
│       ├── reservation.ts
│       ├── catering.ts
│       └── menu.ts
│
├── supabase/
│   └── migrations/                 # Versioned SQL schema files
│
├── architecture.md
├── requirements.md
└── execution-plan.md
```

---

## 6. Database Schema (Summary)

| Table | Purpose |
|---|---|
| `locations` | Restaurant locations — supports future multi-location |
| `restaurant_config` | All business settings per location (hours, fees, rules, timezone) — editable from admin |
| `menu_items` | All menu items — `is_available`, `catering_available`, `allergens` fields included |
| `daily_specials` | Items marked as special for a specific date range |
| `orders` | Pickup and delivery orders — includes `special_instructions`, reference number, `idempotency_key` (unique) |
| `order_items` | Line items per order — price snapshotted at time of order |
| `reservations` | Table bookings — includes reference number, `idempotency_key` (unique) |
| `catering_orders` | Catering event orders — includes reference number, `special_instructions`, `idempotency_key` (unique) |
| `catering_order_items` | Tray items per catering order — price snapshotted |
| `delivery_zones` | Allowed delivery zip codes per location |

**Key schema decisions:**
- All tables with location scope carry `location_id` — ready for multi-location
- Prices snapshotted on `order_items` and `catering_order_items` — past orders unaffected by price changes
- Reference numbers generated via Postgres sequence — format `AKR-YYYYMMDD-XXXX`, guaranteed unique, no race condition
- `restaurant_config` stores: timezone, operating hours, delivery fee, min delivery order, min catering order, catering advance hours, catering deposit percent (default 40), max reservation party size — all editable without code changes
- `menu_items` includes: `allergens[]`, `is_available`, `catering_available`, `catering_price_per_tray`, `display_order`
- Images stay as static frontend files (Phase 1) → Supabase Storage in Phase 2 when admin image upload is needed

**Security model:**
- Public: read menu, validate zip, place orders/reservations/catering (no login)
- Admin (JWT required): read all records, update statuses, cancel, manage menu, manage config, view analytics
- No public sign-up — admin account created manually in Supabase dashboard
- Direct asyncpg connection — backend is sole DB accessor, RLS not required for API routes (RLS still enabled as defence-in-depth)

---

## 7. API Endpoints

### Public (no auth)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Confirms app + DB connection alive |
| GET | `/api/menu` | All active menu items |
| POST | `/api/orders` | Place pickup/delivery order (guest checkout) |
| POST | `/api/reservations` | Make a table reservation |
| POST | `/api/catering` | Place a catering order |
| POST | `/api/delivery/validate` | Check if zip code is in delivery zone |
| POST | `/api/reservations/send-reminders` | Called daily by cron-job.org to send 24h reminders — protected by `X-Cron-Secret` header checked against env variable |

### Admin (Supabase JWT required)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/orders` | List all orders |
| PATCH | `/api/admin/orders/{id}/status` | Update status or cancel |
| GET | `/api/admin/reservations` | List all reservations |
| PATCH | `/api/admin/reservations/{id}/status` | Confirm or cancel |
| GET | `/api/admin/catering` | List all catering orders |
| PATCH | `/api/admin/catering/{id}/status` | Update status or cancel |
| POST | `/api/admin/menu` | Add menu item |
| PUT | `/api/admin/menu/{id}` | Edit menu item |
| DELETE | `/api/admin/menu/{id}` | Remove menu item |
| GET | `/api/admin/analytics` | Monthly sales, pickup vs delivery, top 5 items |
| GET | `/api/admin/config` | Get restaurant config |
| PUT | `/api/admin/config` | Update restaurant config |

> **Admin UI note:** These endpoints are built and tested in Phase 1. The Lovable admin UI (Phase 2) plugs into already-tested endpoints. This ensures the owner can manage the restaurant via API tools from day one.

---

## 8. Business Rules (All Backend Enforced — Values from DB)

| Rule | Enforced in | Config source |
|---|---|---|
| Delivery only to approved zip codes | `delivery_service.py` | `delivery_zones` table |
| Minimum order value for delivery | `order_service.py` | `restaurant_config` |
| Orders only during operating hours | `order_service.py` | `restaurant_config` |
| Scheduled time must be in the future and within operating hours | `order_service.py` | `restaurant_config` |
| Catering minimum order value ($100) | `catering_service.py` | `restaurant_config` |
| Catering orders must be 48h in advance | `catering_service.py` | `restaurant_config` |
| Catering deposit (40%) calculated and returned | `catering_service.py` | `restaurant_config.catering_deposit_percent` — shown in response, email, and success screen; not collected online (Phase 2 — Stripe) |
| Maximum reservation party size (20) | `reservation_service.py` | `restaurant_config` |
| All times validated in restaurant's timezone (Pacific) | All services | `restaurant_config.timezone` |
| No public sign-up | Supabase Auth config | Supabase dashboard |
| Only owner can cancel orders/reservations | `security.py` middleware | Supabase JWT role |
| Rate limit: 10 requests/IP/hour on public POST endpoints | `rate_limit.py` middleware | Code config |
| Duplicate order/reservation/catering prevention | All create services via `idempotency_key` | Frontend-generated UUID sent with every POST; unique constraint in DB; if key already exists, return original response — no duplicate created |

---

## 9. Notification Flow

### Order placed:
1. Validate zip (delivery) + scheduled time within operating hours
2. Save order + items to Supabase, generate reference number (`AKR-YYYYMMDD-XXXX`)
3. Auto-confirm (status = `confirmed`)
4. Send customer confirmation email (full summary: items, prices, total, reference, scheduled time)
5. Send owner notification: email + WhatsApp (full order details)
6. Return reference number to frontend — shown on success screen

### Reservation made:
1. Validate party size ≤ 20, date/time in future
2. Save to Supabase, generate reference number
3. Auto-confirm
4. Send customer confirmation email (if email provided)
5. Send owner notification: email + WhatsApp
6. Return reference number to frontend

### Catering order placed:
1. Validate 48h advance rule + $100 minimum
2. Calculate 40% deposit amount from order total (value from `restaurant_config.catering_deposit_percent`)
3. Save to Supabase, generate reference number
4. Auto-confirm
5. Send customer confirmation email (full summary + deposit amount + "Our team will contact you within 24 hours to arrange payment")
6. Send owner notification: email + WhatsApp (includes deposit amount due)
7. Return reference number + deposit amount to frontend — shown on success screen

### 24-hour reservation reminder:
- cron-job.org pings `POST /api/reservations/send-reminders` daily at 9am Pacific
- Backend queries reservations for the following day
- Sends reminder email to each customer who provided an email address
- Customers without email: silently skipped (no error)

---

## 10. Error Handling (defined in Stage 1, used everywhere)

All API errors return a consistent format:
```json
{
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE"
}
```

Example codes: `INVALID_ZIP`, `OUTSIDE_HOURS`, `CATERING_TOO_SOON`, `BELOW_MIN_ORDER`, `UNAUTHORIZED`

If email or WhatsApp notification fails: order is still saved, error is logged, customer is not affected.

---

## 11. Logging Strategy

All logging via Python's built-in `logging` module configured in `core/logging.py`.

| Environment | Format | Where to view |
|---|---|---|
| Local development | Human-readable (`INFO: Order AKR-... created`) | Terminal |
| Production (Render) | JSON (`{"level":"INFO","event":"order_created","ref":"AKR-..."}`) | Render log viewer (real-time, free) |

**What is logged:**

| Event | Level |
|---|---|
| App startup / shutdown | INFO |
| Every API request + response time | INFO |
| Order / reservation / catering created (reference number only) | INFO |
| Email sent or failed (reference number, reason) | INFO / ERROR |
| WhatsApp sent or failed (reference number, reason) | INFO / ERROR |
| JWT validation failure on admin route | WARNING |
| Rate limit triggered (IP hash only — not full IP) | WARNING |
| Unhandled exceptions | ERROR (full stack trace) |

**What is never logged:** customer name, email, phone, address, or any PII (SEC-10).

---

## 12. Testing Strategy

### Automated tests (pytest + httpx)
Run during development against a real test database. Every service layer function has at least one test. Tests tied to requirement IDs so nothing is missed.

```
tests/
  conftest.py          # shared fixtures, DB setup/teardown
  test_menu.py         # MNU-04: unavailable items excluded
  test_delivery.py     # DLV-01/02/03: valid zip, invalid zip, empty zip
  test_orders.py       # ORD-06/08/10/11/17/19/20: hours, zip, min value, ref number, price snapshot, idempotency (duplicate key = same response, not new order)
                       # Admin: list orders returns correct data, status update persists, cancel sets correct status, invalid JWT returns 401
  test_reservations.py # RES-04/11: party size limit, reference number, idempotency
                       # Admin: list reservations, cancel reservation, invalid JWT returns 401
  test_catering.py     # CAT-03/04: 48h rule, $100 minimum, idempotency
                       # Admin: list catering orders, status update, cancel, invalid JWT returns 401
  test_auth.py         # SEC-02: valid JWT allows write, missing JWT returns 401, expired JWT returns 401, tampered JWT returns 401
  test_admin_config.py # GET /api/admin/config returns current config; PUT updates value; invalid JWT returns 401
  test_analytics.py    # GET /api/admin/analytics returns correct shape (revenue, counts, top items); invalid JWT returns 401
```

**Rule:** mock only at system boundaries (Resend, Twilio HTTP calls). All DB tests hit a real test schema — never mocked.

### Canary monitoring (GitHub Actions + UptimeRobot)
The same pytest tests are environment-aware — controlled by `API_BASE_URL` env variable:
- `API_BASE_URL=http://localhost:8000` → development
- `API_BASE_URL=https://yourapp.onrender.com` → canary against live site

**Canary frequency design:**
- UptimeRobot: `/health` every 5 minutes — free, unlimited, no quota impact. Catches "server is down" immediately.
- GitHub Actions: deeper canary tests every 50 minutes — ~720 minutes/month, well within the 2,000 min/month free tier. pip dependencies are cached to keep each run under 1 minute.
- Both send an alert email to the owner on failure.

### Manual verification
After each slice is deployed, manually verify the full browser flow — place a test order, check Supabase, check email inbox, check WhatsApp.

---

## 13. Frontend Gaps to Fix in Lovable

| # | Page | Gap | Blocks |
|---|---|---|---|
| 1 | OrderPage | Add customer name, email, phone fields | Slice 3 (Orders) |
| 2 | OrderPage | Change "postcode" to "zip code" | Slice 3 (Orders) |
| 3 | OrderPage success screen | Show order reference number | Slice 3 (Orders) |
| 4 | CateringPage | Add customer name, email, phone fields | Slice 5 (Catering) |
| 5 | `RESTAURANT_INFO` in `menu.ts` | Address says "London, UK" — update to real USA address | Slice 1 (Menu) |

> These are **hard prerequisites** for their respective slices — not optional parallel work. Slices 3 and 5 cannot be wired to the frontend until these are done in Lovable.

---

## 14. Build Phases

### Phase 1 — Core Backend (current scope)
- [ ] Supabase schema + seed data
- [ ] FastAPI foundation (Stage 1)
- [ ] All vertical slices (Stage 2)
- [ ] Admin API endpoints (built + tested in Phase 1, UI in Phase 2)
- [ ] Deploy: Render (backend) + Vercel (frontend)

### Phase 2 — Admin UI, Payments & Polish
- [ ] Admin panel UI in Lovable (connects to Phase 1 API)
- [ ] Stripe payment integration
- [ ] Customer order status tracking page
- [ ] Supabase Storage for menu item images (admin upload)
- [ ] Real geocoding for delivery (upgrade from zip code list)
- [ ] Staff logins with role-based access
- [ ] Loyalty / rewards program
- [ ] QR code table ordering
- [ ] Multi-location activation

---

## 15. Additional Architectural Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Restaurant timezone | Pacific Time (America/Los_Angeles) stored in `restaurant_config` | All time validation in restaurant local time. Owner can change via admin panel |
| Reservation reminder mechanism | cron-job.org (free) pings FastAPI endpoint daily | pg_cron cannot make HTTP calls. cron-job.org is free, simple, zero maintenance |
| DB connection | asyncpg direct Postgres connection | Better performance than Supabase client library. No PostgREST intermediary. Use Supabase client only for JWT auth verification |
| Rate limiting | slowapi middleware on all public POST endpoints | Protects against bots and accidental double-submissions |
| Admin endpoints | Built and tested Phase 1, UI wired in Phase 2 | Owner needs day-one ability to manage orders even without a UI |
| Render tier | Free during development, upgrade to $7/mo before go-live | Cold starts are acceptable in dev, not on a live order flow |
| Error format | Defined in Stage 1, used from Slice 1 onward | Prevents retrofitting error handling across 7 slices |
| CORS allowed origins | Set to `VITE_API_URL` (Vercel URL) via env variable — never wildcard `*` | Prevents any other website from making API calls to the backend |
| Cron reminders auth | `X-Cron-Secret` header checked against env variable on `/api/reservations/send-reminders` | Prevents anyone from triggering reminder emails to all customers |
| Canary frequency | UptimeRobot every 5 min (unlimited); GitHub Actions every 50 min (~864 min/month) | Stays within GitHub free tier 2,000 min/month with >1,000 min headroom |
| Idempotency | Frontend generates UUID before each POST; sent as `idempotency_key` in request body; unique constraint in DB; duplicate key returns original response | Prevents duplicate orders from double-clicks, network retries, or browser back-button submissions |

---

## 16. Accounts to Create Before Stage 1

| Service | Purpose | Status | Cost |
|---|---|---|---|
| Supabase | Database + Auth | ❌ Not created | Free |
| Render.com | Python backend hosting | ❌ Not created | Free |
| Vercel | Frontend hosting | ❌ Not created | Free |
| Resend | Email notifications | ❌ Not created | Free |
| Twilio | WhatsApp notifications | ❌ Not created | Free sandbox |
| cron-job.org | Reservation reminder cron | ❌ Not created | Free |
| UptimeRobot | HTTP uptime monitoring on `/health` | ❌ Not created | Free |
| Domain name | Production email sending | ❌ Not purchased | ~$10–15/year — pre-launch only |

---

## 17. Pre-Launch Checklist (before going live with real customers)

- [ ] Upgrade Render to Starter tier ($7/mo) — eliminates cold starts
- [ ] Purchase domain name (~$10–15/year)
- [ ] Configure Resend with custom domain (prevents emails going to spam)
- [ ] Replace Twilio WhatsApp sandbox with approved production number
- [ ] Update `RESTAURANT_INFO` in frontend with real USA address
- [ ] Update delivery zone zip codes with real zip codes
- [ ] Update restaurant config (hours, timezone, fees) with real values
- [ ] Set up Cloudflare (free) on domain DNS — protects Render IP, absorbs volumetric attacks
- [ ] Review privacy/data handling (CCPA applies in California)

---

## 18. Files to Clean Up

| File/Folder | Action |
|---|---|
| `supabase/functions/` | Delete — using FastAPI instead of Edge Functions |
| `supabase/migrations/` | Rewrite with updated schema (locations, restaurant_config, allergens, reference numbers, special_instructions) |
| `supabase/config.toml` | Keep — useful for local development |
| `.env.example` | Rewrite with final Python/FastAPI variables. Remove any PII |

---

## 19. Shared Contracts (Defined Once — Used by All Slices)

These are decisions that every slice must follow. Defined here so each slice spec can reference rather than reinvent.

### Response Convention
- **Success:** Return the domain payload directly — no envelope wrapper.
  - `GET /api/menu` → `{"categories": [...]}`
  - `POST /api/orders` → `{"reference_number": "AKR-...", "status": "confirmed"}`
- **Error:** Always use the error envelope from `core/errors.py`:
  - `{"error": "Human-readable message", "code": "MACHINE_READABLE_CODE"}`
- **Never mix:** a successful response never has an `error` key; an error response never has data keys.

### location_id Strategy
- Phase 1 is single-location. Every DB query uses `DEFAULT_LOCATION_ID` from environment config.
- `core/config.py` reads `DEFAULT_LOCATION_ID` from `.env` and exposes it as `settings.default_location_id`.
- No slice may hardcode a location ID — always read from `settings.default_location_id`.
- When multi-location is activated (Phase 2), this is the only place to change.

### config_service.py — Shared Config Fetching
- Slices 3, 4, 5, and 8 all need values from `restaurant_config` (hours, fees, limits, timezone).
- All must call `get_restaurant_config(db)` from `services/config_service.py` — never write a raw DB query for config in another service.
- Returns a typed `RestaurantConfig` Pydantic model.

### reference_service.py — Reference Number Generation
- Slices 3, 4, and 5 all generate reference numbers in format `AKR-YYYYMMDD-XXXX`.
- All must call `generate_reference_number(db)` from `services/reference_service.py`.
- Uses the Postgres sequence `public.reference_number_seq` — guaranteed unique, no race condition.

### Idempotency Pattern
- Slices 3, 4, and 5 all accept `idempotency_key: UUID` in the request body.
- Pattern is identical for all three:
  1. Check if `idempotency_key` already exists in the table.
  2. If yes: return the original saved response — do not create a new record.
  3. If no: proceed with saving.
- Each service implements this check itself (the table differs), but the logic is identical.

### core/timezone.py — Timezone Utility
- All time validation must happen in the restaurant's local timezone (Pacific Time by default).
- Slices 3, 4, and 5 all validate times — never do raw UTC comparisons.
- All must use `to_restaurant_time(dt, timezone_str)` from `core/timezone.py`.
- Timezone string comes from `restaurant_config.timezone` via `config_service.py`.

### menu_service.py — Item Validation Helper
- When placing an order (Slice 3) or catering order (Slice 5), submitted `menu_item_id` values must be validated.
- `menu_service.py` exposes `validate_menu_items(db, item_ids: list[str]) -> None` — raises `422` if any ID is invalid or unavailable.
- Slice 3 and 5 call this before saving — they do not write their own item-lookup queries.

### Status State Machines
All entities with a `status` column follow these allowed transitions:

| Entity | Initial status | Allowed transitions |
|---|---|---|
| Orders | `confirmed` | `confirmed → ready`, `confirmed → cancelled`, `ready → delivered`, `ready → cancelled` |
| Reservations | `confirmed` | `confirmed → cancelled` |
| Catering orders | `confirmed` | `confirmed → cancelled`, `confirmed → completed` |

Admin endpoints (Slice 8) enforce these transitions — invalid transitions return `422 INVALID_STATUS_TRANSITION`.

### DB Migration Strategy During Development
- **Never edit a migration that has already been applied** to any database (local or Supabase).
- If a slice requires a schema change (new column, new table, new index), add a **new migration file** — additive only.
- Naming convention: `YYYYMMDDNNNNNN_description.sql` — increment the sequence number.
  - Example: `20260406000003_slice3_add_scheduled_time_to_orders.sql`
- Each migration file must be idempotent where possible (use `IF NOT EXISTS`, `IF EXISTS`).
- Applied migrations are append-only history — treat them like git commits, never rewrite history.
