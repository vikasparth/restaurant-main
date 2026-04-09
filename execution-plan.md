# Execution Plan — Aap ki Rasoi Backend
**Status: APPROVED — Signed off by Vikas, 2026-04-06**
**Last updated: 2026-04-09**
**Reference:** See `architecture.md` for full design decisions.

---

## Guiding Principles

- **Plan → Approve → Build → Test** — in that order, every time
- Never start the next stage until the current one is tested and working
- One vertical slice at a time — fully working end-to-end before moving on
- Show a 2–3 line summary of what will be built, wait for approval, then build
- Token efficiency: keep context lean — reference `architecture.md` for design detail

---

## Pre-conditions (must be resolved before Stage 1)

### Architecture sign-off
- [x] Owner reviews and approves `architecture.md` ✅ 2026-04-06

### Accounts to create (all free)
- [x] Create Supabase account — supabase.com (GitHub login) ✅
- [x] Create Render.com account — render.com (GitHub login) ✅
- [x] Create Vercel account — vercel.com (GitHub login) ✅
- [x] Create Resend account — resend.com (GitHub login) ✅
- [x] Create Twilio account — twilio.com (email login) ✅
- [x] Create cron-job.org account (email login) ✅
- [x] Create UptimeRobot account (email login) ✅

### Cleanup
- [x] Delete `supabase/functions/` folder — was never created, already clean ✅
- [x] Rewrite `supabase/migrations/` with updated schema (locations, restaurant_config, allergens, daily_specials, reference numbers, idempotency keys) ✅
- [x] Rewrite `.env.example` with final variables ✅

### Frontend gaps to fix in Lovable (can run in parallel with Stage 1)
- [ ] OrderPage: add customer name, email, phone fields
- [ ] OrderPage: change "postcode" placeholder to "zip code"
- [ ] CateringPage: add customer name, email, phone fields
- [ ] OrderPage success screen: show order reference number
- [ ] Update `RESTAURANT_INFO` address from London, UK to real USA address

---

## Stage 1 — Foundation
> Build the skeleton that all features share. Nothing feature-specific.
> **Done when:** `GET /health` returns `{"status": "ok"}` and Supabase connection is confirmed.

| # | Task | Description | Status |
|---|---|---|---|
| 1.1 | Python environment setup | `backend/` folder, `requirements.txt`, virtual env | ✅ Done |
| 1.2 | FastAPI app skeleton | `main.py` with CORS (allowed origins from env variable — never wildcard), router registration, startup event | ✅ Done |
| 1.3 | Config / env setup | `core/config.py` reads all `.env` variables with validation | ✅ Done |
| 1.4 | Global error handling | `core/errors.py` — defines consistent `{"error": "...", "code": "..."}` format used by all routes | ✅ Done |
| 1.5 | Auth middleware | `core/security.py` — Supabase JWT verification for all admin routes | ✅ Done |
| 1.6 | Rate limiting setup | `core/rate_limit.py` — slowapi middleware on public POST endpoints | ✅ Done |
| 1.7 | Supabase DB connection | `core/database.py` — asyncpg session pooler connection (IPv6 issue on direct connection) | ✅ Done |
| 1.8 | Health check endpoint | `GET /health` → confirms app + DB alive | ✅ Done |
| 1.9 | Database schema applied | Run updated migrations on Supabase | ✅ Done |
| 1.10 | Seed data applied | Seed: 1 location, initial restaurant_config, sample menu items, sample zip codes | ✅ Done |
| 1.11 | Structured logging setup | `core/logging.py` — JSON logs in production, human-readable in dev; log business events, errors, rate limit triggers; never log PII | ✅ Done |
| 1.12 | Test suite setup | Install pytest + httpx; create `tests/` folder with `conftest.py`; write one sample test to confirm setup works | ✅ Done |
| 1.13 | Local run verified | `uvicorn main:app --reload` works, `/health` passes, one test passes | ✅ Done |

---

## Stage 2 — Vertical Slices (Feature by Feature)

> For each feature, build the complete stack before moving to the next:
> `Pydantic model → Service logic → Router → Frontend service → Wire to UI page → Test`

### Rules for Every Slice
- **Full test suite runs after every slice** — not just that slice's tests. If any prior test breaks, fix it before moving on. This is the primary guard against integration failures.
- **Spec must be signed off before any code is written** — see `specs/sliceN_name.md`
- **Never edit an already-applied migration** — if a slice needs a schema change, add a new migration file named `20260406000003_sliceN_description.sql` (additive only)

### Collaboration Model for Stage 2
Stage 2 is a **pair programming partnership** between the owner (new engineer learning to code) and Claude (senior engineer/architect):

- **Incremental steps** — one small piece at a time (one function, one endpoint, never a whole file at once)
- **Claude explains first** — before any code is written, I explain what needs to be done and why
- **Owner writes where possible** — you are encouraged to write code yourself as a learning exercise
- **Claude suggests and completes** — I suggest code snippets, explain each line, and fill in what you're not ready for yet
- **No large code dumps** — we build together step by step so you understand everything that goes in
- **Questions are encouraged** — ask about anything at any time; learning Python is a goal of this project
- **Claude writes boilerplate/config** — I handle repetitive setup (imports, config, wiring) so you can focus on learning meaningful logic

---

### Slice 1 — Menu (Read)
> Enables frontend to load menu from database instead of static file.

| # | Task | Description | Status |
|---|---|---|---|
| 2.1.1 | Pydantic model | `models/menu.py` — MenuItem, Category | ⏳ Pending |
| 2.1.2 | Menu service | `services/menu_service.py` — fetch all active items from Supabase | ⏳ Pending |
| 2.1.3 | Menu router | `routers/menu.py` — `GET /api/menu` | ⏳ Pending |
| 2.1.4 | Frontend service | `src/services/menuService.ts` — fetch from API | ⏳ Pending |
| 2.1.5 | Wire to UI | Update `MenuPage.tsx` + `CartContext` to use API instead of static `menu.ts` | ⏳ Pending |
| 2.1.6 | Automated tests | pytest: menu returns items, categories correct, unavailable items excluded | ⏳ Pending |
| 2.1.7 | Manual verification | Menu loads in browser from database | ⏳ Pending |

---

### Slice 2 — Delivery Validation
> Validates customer zip code before allowing delivery order.

| # | Task | Description | Status |
|---|---|---|---|
| 2.2.1 | Pydantic model | `models/delivery.py` — DeliveryValidateRequest/Response | ⏳ Pending |
| 2.2.2 | Delivery service | `services/delivery_service.py` — check zip against `delivery_zones` table | ⏳ Pending |
| 2.2.3 | Delivery router | `routers/delivery.py` — `POST /api/delivery/validate` | ⏳ Pending |
| 2.2.4 | Frontend service | `src/services/deliveryService.ts` | ⏳ Pending |
| 2.2.5 | Wire to UI | Update `OrderPage.tsx` to validate zip before showing delivery option | ⏳ Pending |
| 2.2.6 | Automated tests | pytest: valid zip accepted, invalid zip rejected, empty zip rejected | ⏳ Pending |
| 2.2.7 | Manual verification | Valid zip accepted, invalid zip shows friendly error in browser | ⏳ Pending |

---

### Slice 3 — Orders
> Core feature — saves pickup/delivery orders to database.

| # | Task | Description | Status |
|---|---|---|---|
| 2.3.1 | Spec | `specs/slice3_orders.md` — 18 tests defined, business rules captured, signed off | ✅ Done 2026-04-09 |
| 2.3.2 | Automated tests | `tests/test_orders.py` — 18 tests written, all failing (TDD Step 1) | ✅ Done 2026-04-09 |
| 2.3.3 | Pydantic model | `models/order.py` — `OrderItemRequest`, `OrderCreateRequest`, `OrderCreateResponse` | ✅ Done 2026-04-09 |
| 2.3.4 | Order service | `services/order_service.py` — validate hours, zip, min order, items; save order + items; idempotency | ⏳ Pending |
| 2.3.5 | Orders router | `routers/orders.py` — `POST /api/orders` | ⏳ Pending |
| 2.3.6 | Run tests | All 18 tests green | ⏳ Pending |
| 2.3.7 | Frontend service | `src/services/orderService.ts` | ⏳ Pending |
| 2.3.8 | Wire to UI | Update `OrderPage.tsx` — add name/email/phone, generate idempotency_key, show reference number | ⏳ Pending |
| 2.3.9 | Manual verification | Full order flow in browser: place order → see reference number → check Supabase | ⏳ Pending |

---

### Slice 4 — Reservations
> Saves table reservation requests to database.

| # | Task | Description | Status |
|---|---|---|---|
| 2.4.1 | Pydantic model | `models/reservation.py` — includes `idempotency_key: UUID` | ⏳ Pending |
| 2.4.2 | Reservation service | `services/reservation_service.py` — save to Supabase; idempotency check on key | ⏳ Pending |
| 2.4.3 | Reservations router | `routers/reservations.py` — `POST /api/reservations` | ⏳ Pending |
| 2.4.4 | Frontend service | `src/services/reservationService.ts` | ⏳ Pending |
| 2.4.5 | Wire to UI | Update `ReservationPage.tsx` to POST to API | ⏳ Pending |
| 2.4.6 | Automated tests | pytest: reservation saved, party size limit enforced, reference number generated, idempotency check | ⏳ Pending |
| 2.4.7 | Manual verification | Reservation saved in Supabase, confirmation shown in browser | ⏳ Pending |

---

### Slice 5 — Catering Orders
> Saves catering orders, enforces 48-hour advance rule.

| # | Task | Description | Status |
|---|---|---|---|
| 2.5.1 | Pydantic model | `models/catering.py` — includes `idempotency_key: UUID` | ⏳ Pending |
| 2.5.2 | Catering service | `services/catering_service.py` — 48h validation, $100 minimum, calculate 40% deposit amount from `restaurant_config.catering_deposit_percent`, save to Supabase; idempotency check on key | ⏳ Pending |
| 2.5.3 | Catering router | `routers/catering.py` — `POST /api/catering` | ⏳ Pending |
| 2.5.4 | Frontend service | `src/services/cateringService.ts` | ⏳ Pending |
| 2.5.5 | Wire to UI | Update `CateringPage.tsx` to POST to API | ⏳ Pending |
| 2.5.6 | Automated tests | pytest: catering saved, 48h rule enforced, minimum order enforced, idempotency check | ⏳ Pending |
| 2.5.7 | Manual verification | Full catering flow in browser, reference number + deposit amount shown on success screen | ⏳ Pending |

---

### Slice 6 — Notifications
> Add email + WhatsApp notifications to Orders, Reservations, and Catering.

| # | Task | Description | Status |
|---|---|---|---|
| 2.6.1 | Email service | `services/email_service.py` — Resend wrapper, confirmation templates | ⏳ Pending |
| 2.6.2 | WhatsApp service | `services/whatsapp_service.py` — Twilio wrapper | ⏳ Pending |
| 2.6.3 | Wire to orders | Call email + WhatsApp after order saved | ⏳ Pending |
| 2.6.4 | Wire to reservations | Call email + WhatsApp after reservation saved | ⏳ Pending |
| 2.6.5 | Wire to catering | Call email + WhatsApp after catering order saved | ⏳ Pending |
| 2.6.6 | Automated tests | pytest: email/WhatsApp failures do not block order save (REL-02, REL-03); failure logged | ⏳ Pending |
| 2.6.7 | Manual verification | Customer receives confirmation email, owner receives WhatsApp message | ⏳ Pending |

---

### Slice 7 — Menu Admin CRUD
> Owner can add, edit, and remove menu items via API (used by admin UI).

| # | Task | Description | Status |
|---|---|---|---|
| 2.7.1 | Auth middleware | `core/security.py` — verify Supabase JWT on protected routes | ⏳ Pending |
| 2.7.2 | Admin menu service | Extend `menu_service.py` with create/update/delete | ⏳ Pending |
| 2.7.3 | Admin menu router | `POST`, `PUT`, `DELETE` on `/api/menu` (admin only) | ⏳ Pending |
| 2.7.4 | Automated tests | pytest: valid JWT allows write; missing/invalid JWT returns 401; public GET still works unauthenticated | ⏳ Pending |
| 2.7.5 | Manual verification | Admin can add/edit/delete items via API; unauthenticated request is rejected | ⏳ Pending |

---

### Slice 8 — Admin Endpoints (Orders, Reservations, Catering, Config, Analytics)
> Owner can view and manage all records via API. Required for day-one operations before admin UI is built in Phase 2.

| # | Task | Description | Status |
|---|---|---|---|
| 2.8.1 | Admin orders service | Extend `order_service.py` — list all orders, update status, cancel | ⏳ Pending |
| 2.8.2 | Admin reservations service | Extend `reservation_service.py` — list all, cancel | ⏳ Pending |
| 2.8.3 | Admin catering service | Extend `catering_service.py` — list all, update status, cancel | ⏳ Pending |
| 2.8.4 | Analytics service | `services/analytics_service.py` — monthly revenue, pickup vs delivery count, top 5 items | ⏳ Pending |
| 2.8.5 | Admin config service | Read and update `restaurant_config` (hours, fees, rules) | ⏳ Pending |
| 2.8.6 | Admin router | Wire all above into `routers/admin.py` behind JWT middleware | ⏳ Pending |
| 2.8.7 | Automated tests | pytest — in `test_orders.py`: list returns saved orders, status update persists, cancel sets correct status, invalid JWT returns 401; in `test_reservations.py`: list returns reservations, cancel works, invalid JWT returns 401; in `test_catering.py`: list + cancel + invalid JWT; new `test_admin_config.py`: GET returns config, PUT updates value, invalid JWT returns 401; new `test_analytics.py`: returns correct shape and values, invalid JWT returns 401 | ⏳ Pending |
| 2.8.8 | Manual verification | Call each admin endpoint via API tool (e.g. Postman/curl); verify correct data returned | ⏳ Pending |

---

## Stage 3 — Cross-Cutting Concerns

| # | Task | Description | Status |
|---|---|---|---|
| 3.1 | Global error handling | Consistent error response format across all endpoints | ⏳ Pending |
| 3.2 | Input validation review | Review all Pydantic models for edge cases | ⏳ Pending |
| 3.3 | Deploy backend to Render | Connect GitHub repo, set env vars, verify live URL | ⏳ Pending |
| 3.4 | Deploy frontend to Vercel | Connect GitHub repo, set `VITE_API_URL` to Render URL | ⏳ Pending |
| 3.5 | End-to-end smoke test | Full order flow on production URLs | ⏳ Pending |
| 3.6 | Canary monitoring setup | UptimeRobot HTTP check on `/health` every 5 min (unlimited); GitHub Actions runs canary tests every 50 min (~864 min/month, well within free tier); alert to owner email on failure | ⏳ Pending |

---

## Canary Monitoring Strategy

> Automated synthetic tests that run against the deployed website on a schedule to detect outages before customers do.

### Approach
The same pytest integration tests used during development are made **environment-aware** — pointed at the live Render URL instead of localhost. A GitHub Actions workflow (free, 2000 min/month) runs them on a schedule.

```
tests/
  canary/
    test_health.py          # GET /health → 200, {"status": "ok"}
    test_menu_available.py  # GET /api/menu → 200, non-empty array
    test_delivery_check.py  # POST /api/delivery/validate with known valid zip → 200
```

Controlled by one env variable: `API_BASE_URL=https://yourapp.onrender.com`

### Alert Channels
| Tool | What it monitors | Frequency | Cost |
|---|---|---|---|
| **UptimeRobot** | Raw HTTP uptime on `/health` | Every 5 min | Free, unlimited |
| **GitHub Actions** | Canary test suite (menu, delivery, health) | Every 50 min | ~864 min/month — within 2,000 free tier |
| Both alert to | Owner email on failure | — | — |

### What canary tests catch
- Backend crashed or Render deployment failed
- Database connection lost
- Menu endpoint returning empty (data issue)
- Delivery validation broken after a code change
- Cold start taking too long (Render timeout)

### What canary tests do NOT test
- Full browser flow (that's Playwright/Selenium — Phase 2 if needed)
- Email/WhatsApp delivery (tested manually after each slice)

---

## Phase 2 — Future (not in current scope)

- [ ] Stripe payment integration
- [ ] Customer order status tracking page
- [ ] Real geocoding for delivery radius (upgrade from zip code list)
- [ ] Admin panel API endpoints (once Lovable UI is ready)
- [ ] Upgrade Render to paid tier if cold starts become a problem
