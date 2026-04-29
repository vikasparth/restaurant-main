# Execution Plan — Completed Items
**Purpose: Reference for finished work. Active plan is in `execution-plan.md`.**
**Last updated: 2026-04-29**

---

## Pre-conditions (Resolved)

### Architecture sign-off
- [x] Owner reviews and approves `docs/architecture.md` ✅ 2026-04-06

### Accounts created (all free)
- [x] Supabase ✅
- [x] Render.com ✅
- [x] Vercel ✅
- [x] Resend ✅
- [x] Twilio ✅
- [x] cron-job.org ✅
- [x] UptimeRobot ✅

### Cleanup
- [x] Delete `supabase/functions/` folder ✅
- [x] Rewrite `supabase/migrations/` with updated schema (locations, restaurant_config, allergens, daily_specials, reference numbers, idempotency keys) ✅
- [x] Rewrite `.env.example` with final variables ✅

---

## Stage 1 — Foundation ✅ Complete

| # | Task | Status |
|---|---|---|
| 1.1 | Python environment setup — `backend/`, `requirements.txt`, virtual env | ✅ Done |
| 1.2 | FastAPI app skeleton — CORS, router registration, startup event | ✅ Done |
| 1.3 | Config / env setup — `core/config.py` | ✅ Done |
| 1.4 | Global error handling — `core/errors.py` | ✅ Done |
| 1.5 | Auth middleware — `core/security.py` | ✅ Done |
| 1.6 | Rate limiting — `core/rate_limit.py` | ✅ Done |
| 1.7 | Supabase DB connection — asyncpg session pooler (IPv6 workaround) | ✅ Done |
| 1.8 | Health check — `GET /health` | ✅ Done |
| 1.9 | Database schema applied | ✅ Done |
| 1.10 | Seed data applied | ✅ Done |
| 1.11 | Structured logging — `core/logging.py` | ✅ Done |
| 1.12 | Test suite setup — pytest + httpx, `tests/conftest.py` | ✅ Done |
| 1.13 | Local run verified | ✅ Done |

---

## Stage 2 — Completed Slices

### Slice 1 — Menu (Read) ✅
`models/menu.py`, `services/menu_service.py`, `routers/menu.py`, `src/services/menuService.ts`, `MenuPage.tsx` wired to API, tests passing, manual verified.

### Slice 2 — Delivery Validation ✅
`models/delivery.py`, `services/delivery_service.py`, `routers/delivery.py`, `src/services/deliveryService.ts`, `OrderPage.tsx` zip validation, tests passing, manual verified.

### Slice 3 — Orders ✅ Done 2026-04-09
Spec signed off (`backend/specs/slice3_orders.md`, 18 tests). `models/order.py`, `services/order_service.py` (hours, zip, min order, idempotency), `routers/orders.py`. Frontend `orderService.ts`, `OrderPage.tsx` (name/email/phone, reference number). All 18 tests green, manual verified.

### Slice 4 — Reservations ✅ Done 2026-04-12
Spec signed off (`backend/specs/slice4_reservations.md`, 10 tests). `models/reservation.py`, `services/reservation_service.py`, `routers/reservations.py`. Frontend `reservationService.ts`, `ReservationPage.tsx`. All 10 tests green, manual verified.

### Slice 5 — Catering Orders ✅ Done 2026-04-12
`models/catering.py`, `services/catering_service.py` (48h rule, zip, $100 min, 40% deposit from config, idempotency), `routers/catering.py`. Frontend `cateringService.ts`, `CateringPage.tsx`. 11 tests green, manual verified.

### Slice 6 — Notifications ✅ Done 2026-04-13
`services/email_service.py` (Resend), `services/whatsapp_service.py` (Twilio), wired to orders + reservations + catering. Failures do not block saves (REL-02, REL-03), failures logged. Manual verified with real Resend key + Twilio sandbox.

---

## Stage 3 — Completed Items

| # | Task | Completed |
|---|---|---|
| 3.3 | Deploy backend to Render | ✅ 2026-04-13 |
| 3.4 | Deploy frontend to Vercel | ✅ 2026-04-13 |
| 3.5 | End-to-end smoke test | ✅ 2026-04-13 |
| 3.6 | Canary monitoring — UptimeRobot (5 min) + GitHub Actions (50 min) | ✅ 2026-04-14 |
| 3.7 | Sentry frontend — `@sentry/browser`, `src/lib/logger.ts` | ✅ 2026-04-27 |
| 3.8 | Runbook skeleton — `backend/docs/runbook.md` | ✅ 2026-04-14 |
| 3.9 | Request logging middleware — `request_logs` DB table | ✅ 2026-04-14 |
| 3.10 | Notification failure logging — `notification_logs` DB table | ✅ 2026-04-14 |
| 3.11 | AI monitoring agent Phase 1 (rule-based) — cron-job.org → `/api/internal/monitor`, GitHub Issue on breach, email alert | ✅ 2026-04-15 — ⚠️ Follow-up: second live test returned 200 but no issue/email created; check Render logs + GITHUB_TOKEN/GITHUB_REPO env vars + `alerts_fired` in response |
| 3.12 | Skill: `/monitor-check` — on-demand MCP-based health check | ✅ 2026-04-16 |
| 3.13 | AI monitoring agent Phase 2 (MCP) — 6 tools in `backend/mcp_server.py` | ✅ 2026-04-16 — ⚠️ Open: MCP not connecting in VSCode extension (v2.1.112); workaround: `claude --mcp-config .claude/settings.json` from terminal |
| 3.17 | Homepage dynamic content — Index.tsx reads Meal of the Day + Latest Offers from GraphQL | ✅ 2026-04-24 |

---

## Developer Tooling — Completed

| # | Item | Completed |
|---|---|---|
| DT-1 | Pre-commit hooks — frontend (Husky + lint-staged) | ✅ 2026-04-21 |
| DT-2 | Pre-commit hooks — backend (Black + Flake8) | ✅ 2026-04-21 |
| DT-3 | Local dev setup README | ✅ 2026-04-21 |
| DT-4 | Skill: `/requirements` with guardrails and draft/sign-off | ✅ 2026-04-21 |
| DT-9 | CI pipeline — GitHub Actions (TypeScript compile + ESLint + build on every push/PR) | ✅ 2026-04-24 |

---

## GraphQL Gateway — Completed Items

| # | Task | Completed |
|---|---|---|
| 3.16.1 | Architecture decisions — Option B (hand-written schema), `graphql-gateway/` at repo root, dual Vercel deploy | ✅ Done |
| 3.16.2 | Apollo Server setup — Apollo 4.x, `tsx`, `dotenv`, `config.ts` | ✅ 2026-04-24 |
| 3.16.3 | Menu schema — `graphql-gateway/schemas/menu.graphql` | ✅ 2026-04-24 |
| 3.16.4 | Menu resolvers — `graphql-gateway/resolvers/menu.ts` | ✅ 2026-04-24 |
| 3.16.5 | graphql-codegen — `codegen.ts`, generates `src/__generated__/menu.ts` | ✅ 2026-04-24 |
| 3.16.6 | Menu component migration — `useMenu` hook, `MenuPage.tsx`, `Index.tsx`, `src/features/menu/` | ✅ 2026-04-24 |
| 3.16.7 | CI schema validator — `validate-schema.js` checks GraphQL fields against `openapi.json` | ✅ 2026-04-25 |
| 3.16.8 | graphql-inspector in CI — detects breaking schema changes | ✅ 2026-04-25 |
| 3.16.9 | Sentry gateway SDK — `@sentry/node` in gateway | ✅ 2026-04-27 |
| 3.16.10 | Orders GraphQL migration — schema + resolver + `useOrders` hook + `OrderPage.tsx` | ✅ 2026-04-26 |
| 3.16.12 | Reservations GraphQL migration — schema + resolver + `useReservations` hook + `ReservationPage.tsx` | ✅ 2026-04-26 |

---

## Canary Monitoring Reference

> Documents the live monitoring infrastructure for context when updating in Phase 4.2.

```
backend/tests/canary/
    test_health.py          # GET /health → 200, {"status": "ok"}
    test_menu_available.py  # GET /api/menu → 200, non-empty array
    test_delivery_check.py  # POST /api/delivery/validate with known valid zip → 200
```

Controlled by: `API_BASE_URL=https://restaurant-main.onrender.com`
Workflow: `.github/workflows/canary.yml` — runs every 50 min (~864 min/month, within 2,000 free tier)
UptimeRobot: HTTP check on `/health` every 5 min
Both alert to owner email on failure.
