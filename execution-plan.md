# Execution Plan — Aap ki Rasoi (Active)
**Status: APPROVED — Signed off by Vikas, 2026-04-06**
**Last updated: 2026-04-29**
**Reference:** `docs/architecture.md` for design decisions.
**Completed work:** `execution-plan-completed.md` — all finished stages, slices, and tooling items.

---

## Guiding Principles

- **Plan → Approve → Build → Test** — in that order, every time
- Never start the next stage until the current one is tested and working
- One vertical slice at a time — fully working end-to-end before moving on
- Show a 2–3 line summary of what will be built, wait for approval, then build
- Token efficiency: keep context lean — reference `docs/architecture.md` for design detail

---

## Open Pre-conditions

### Frontend gaps to fix in Lovable
- [ ] OrderPage: add customer name, email, phone fields
- [ ] OrderPage: change "postcode" placeholder to "zip code"
- [ ] CateringPage: add customer name, email, phone fields
- [ ] OrderPage success screen: show order reference number
- [ ] Update `RESTAURANT_INFO` address from London, UK to real USA address

---

## Stage 2 — Remaining Slices

> Slices 1–6 complete. See `execution-plan-completed.md`.

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
> Owner can view and manage all records via API. Required for day-one operations before admin UI is built.

| # | Task | Description | Status |
|---|---|---|---|
| 2.8.1 | Admin orders service | Extend `order_service.py` — list all orders, update status, cancel | ⏳ Pending |
| 2.8.2 | Admin reservations service | Extend `reservation_service.py` — list all, cancel | ⏳ Pending |
| 2.8.3 | Admin catering service | Extend `catering_service.py` — list all, update status, cancel | ⏳ Pending |
| 2.8.4 | Analytics service | `services/analytics_service.py` — monthly revenue, pickup vs delivery count, top 5 items | ⏳ Pending |
| 2.8.5 | Admin config service | Read and update `restaurant_config` (hours, fees, rules) | ⏳ Pending |
| 2.8.6 | Admin router | Wire all above into `routers/admin.py` behind JWT middleware | ⏳ Pending |
| 2.8.7 | Automated tests | `test_orders.py`: list, status update, cancel, 401. `test_reservations.py`: list, cancel, 401. `test_catering.py`: list, cancel, 401. `test_admin_config.py`: GET/PUT/401. `test_analytics.py`: shape + values + 401 | ⏳ Pending |
| 2.8.8 | Manual verification | Call each admin endpoint via Postman/curl; verify correct data returned | ⏳ Pending |

---

## Stage 3 — Remaining Items

> Completed: 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.17. See `execution-plan-completed.md`.
> **Remaining sequence:** 3.1 + 3.2 → 3.14 → 3.15 → remaining 3.16 items

| # | Task | Description | Status |
|---|---|---|---|
| 3.1 | Global error handling | Consistent error response format across all endpoints | ⏳ Pending |
| 3.2 | Input validation review | Review all Pydantic models for edge cases | ⏳ Pending |
| 3.14 | Sentry backend SDK | Install `sentry-sdk[fastapi]`; auto-capture unhandled exceptions with request context (URL, method, correlation ID) | ⏳ Pending |
| 3.15 | Two-team ownership setup | Export `openapi.json`, contract rules in CLAUDE.md files, `lovable_project/CLAUDE.md` | ⏳ Pending |

---

## GraphQL Gateway — Remaining Items

> Completed: 3.16.1–3.16.10, 3.16.12, 3.16.9. See `execution-plan-completed.md`.

| # | Task | Description | Status |
|---|---|---|---|
| 3.16.11 | Catering GraphQL migration | Schema + resolver + `useCatering` hook; migrate `CateringPage.tsx` | ⏳ Pending |
| 3.16.13 | Deploy gateway to Vercel | `graphql-gateway/api/graphql.ts` (Vercel-native handler), `vercel.json` rewrite; `api/graphql.ts` not being registered as serverless function — root cause not yet found | 🔄 In Progress |
| 3.16.14 | Set VITE_GATEWAY_URL in frontend Vercel | Point frontend at deployed gateway URL; fixes blank production page | ⏳ Blocked on 3.16.13 |
| 3.16.15 | Revert allergens bug in useMenu.ts | Add `allergens` back to the GraphQL query — was deliberately removed for Sentry exercise | ⏳ Pending |

**Feature folder convention:** Migrate one feature at a time to `src/features/[feature]/` only when it moves to GraphQL. See `src/docs/feature-migration-guide.md`.

---

## Developer Tooling — Pending

> Completed: DT-1, DT-2, DT-3, DT-4, DT-9. See `execution-plan-completed.md`.

| # | Item | Status |
|---|---|---|
| DT-5 | Skill: `/review` — codebase review before any new feature | ✅ Done — ⏳ Not yet tested |
| DT-6 | Skill: `/design` | ⏳ Pending |
| DT-7 | Skill: `/spec` | ⏳ Pending |
| DT-8 | Skill: `/execution-plan` | ⏳ Pending |
| DT-10 | Unit + integration tests — menu slice (backend + frontend) | ⏳ Pending |
| DT-11 | **⚠️ Must have — Claude Code token efficiency** | Context window exhaustion is a development blocker. Build a plugin/skill that surfaces live token usage per session, identifies patterns that inflate context (large file reads, over-broad globs, repeated context re-reads), and recommends lean context habits, `/compact` timing, session scoping. Goal: no session hits the token ceiling mid-task. | ⏳ Pending |
| DT-12 | Per-project env setup | Each sub-project owns its own `.env.example` — separate teams, separate secrets. **(1)** Create `backend/.env.example` (FastAPI vars); **(2)** create `graphql-gateway/.env.example` (gateway vars); **(3)** create `agents/.env.example` (`ANTHROPIC_API_KEY`, `SENTRY_AUTH_TOKEN`, `SENTRY_ORG_SLUG`, `RENDER_API_KEY`, `GITHUB_TOKEN`); **(4)** trim root `.env.example` to frontend-only vars (`VITE_*`); **(5)** add `python-dotenv` to `agents/requirements.txt` and `load_dotenv()` to `agents/config.py`; **(6)** update README with a setup section per sub-project so a new engineer or GenAI agent can onboard from the README alone | ✅ Done |
| DT-13 | Agent observability — token usage + confidence via Sentry | Wrap each agent `run()` in a Sentry Performance transaction; record `input_tokens`, `output_tokens`, `total_tokens`, `turns_used`, `confidence`, `status` as custom measurements; add `agent` tag for per-agent filtering; build Sentry dashboard with token usage trend and confidence distribution charts. Enables token budget tuning and correlation between token spend and finding quality. | ⏳ Pending |

---

## Phase 3 — Agentic Workflows

> **Architecture:** `docs/engineering-practices/agent-architecture.md`
> **Implementation plan:** `docs/engineering-practices/agent-execution-plan.md`
> **Workflow context:** `docs/engineering-practices/ai-agent-workflow.md`

| Task | Detail | Status |
|---|---|---|
| Phase A — Prerequisites | A.1 ✅ A.2 ✅ A.3 ✅ A.4 ✅ A.5 ✅ — A.6 (Render API access) ⏳ A.7 ✅ | 🔄 In Progress |
| Phase D — Individual Agents | D.1 Frontend Sentry ✅ — D.2 Backend Sentry ⏳ D.3 Render Logs ⏳ D.4 GitHub ⏳ D.5 Codebase ⏳ D.6 Recommendation ⏳ | 🔄 In Progress |
| Phase C — Orchestration Layer | Orchestrator, `/troubleshoot` skill, `sentry-monitor-frontend.yml`, `sentry-monitor-backend.yml`, GitHub write authorization | ⏳ Pending |
| Phase D — Validation | End-to-end validation against all 5 test scenarios + false positive check | ⏳ Pending |

---

## Phase 4 — Infrastructure & Reliability

### 4.1 — Queue / Notification Integration

> Replace direct Resend/Twilio calls with an async queue layer. Adds retry with backoff and dead-letter handling.
> **Current state:** `email_service.py` + `whatsapp_service.py` called synchronously from order/reservation/catering services — no retry.

| # | Task | Description | Status |
|---|---|---|---|
| 4.1.1 | Choose queue backend | AWS SQS (1M req/month free) vs Redis Queue vs Celery + Redis — decide alongside 4.2 compute choice; document as ADR | ⏳ Pending |
| 4.1.2 | Queue service | `services/queue_service.py` — enqueue email and WhatsApp jobs separately; payload: type, recipient, reference number, template key (no excess PII) | ⏳ Pending |
| 4.1.3 | Worker | Dequeues jobs, calls Resend/Twilio, retries max 3 attempts with exponential backoff, moves to dead-letter after final failure | ⏳ Pending |
| 4.1.4 | Dead-letter handling | Consumer logs failure to `notification_logs` with full retry history; triggers owner email alert — no notification silently lost | ⏳ Pending |
| 4.1.5 | Wire to slices | Replace direct email/WhatsApp calls in order, reservation, catering services with queue enqueue | ⏳ Pending |
| 4.1.6 | Automated tests | Job enqueued on save; worker delivers on dequeue; failed delivery retries to max; dead-letter created; `notification_logs` updated correctly | ⏳ Pending |
| 4.1.7 | Manual verification | Place order → confirm queue → confirm delivery → simulate failure → confirm retry → confirm dead-letter alert | ⏳ Pending |

---

### 4.2 — AWS DevOps Pipeline (Free Tier)

> Migrate from Render + Vercel to AWS. CI/CD with CodePipeline + CodeBuild, backend on AWS compute, frontend on S3 + CloudFront.

**AWS free tier — accurate:**

| Service | Free allowance | Duration |
|---|---|---|
| Lambda | 1M requests + 400K GB-seconds/month | Always free |
| API Gateway (HTTP API) | 1M requests/month | 12 months only |
| EC2 t2.micro | 750 hrs/month | 12 months only |
| Elastic Beanstalk | Free (EC2 underneath is not) | — |
| S3 | 5 GB storage, 20K GET, 2K PUT/month | 12 months only |
| CloudFront | 1 TB transfer + 10M requests/month | Always free |
| CodeBuild | 100 build minutes/month | Always free |
| CodePipeline | 1 active pipeline/month | Always free |
| ECR (public) | Unlimited | Always free |
| Parameter Store (standard) | 10,000 parameters | Always free |
| **ECS Fargate** | **~$10–15/month minimum** | ❌ Not free tier |
| **Secrets Manager** | **$0.40/secret/month** | ❌ Not free tier |

**Compute choice:**

| Option | Cost | Trade-off |
|---|---|---|
| **Lambda + API Gateway** (recommended) | Always free within limits | Requires Mangum adapter to wrap FastAPI; cold starts after idle |
| **EC2 t2.micro + Elastic Beanstalk** | Free 12 months, then ~$10/month | No code change; warm instance; cost kicks in after year 1 |

**Nice to Have — evaluate at implementation time (paid):**
- [ ] ECS Fargate — container-native, no EC2 management; ~$10–15/month; consider if cold starts/scaling become a problem
- [ ] Secrets Manager — automatic rotation; $0.40/secret/month; consider if compliance requirements arise

| # | Task | Description | Status |
|---|---|---|---|
| 4.2.1 | Architecture decision | Lambda + API Gateway vs EC2 + Elastic Beanstalk; document as ADR | ⏳ Pending |
| 4.2.2 | Backend adapter / Dockerfile | Lambda: add Mangum, `handler.py` entry point, package as zip or ECR image. EB: `Dockerfile` multi-stage, uvicorn, non-root | ⏳ Pending |
| 4.2.3 | ECR setup (public) | Create public ECR repo (always free); push image tagged to Git SHA for Sentry release traceability | ⏳ Pending |
| 4.2.4 | Compute setup | Lambda: function + HTTP API Gateway + `/health` check. EB: environment, t2.micro, health check on `/health` | ⏳ Pending |
| 4.2.5 | Secrets via Parameter Store | Migrate all secrets to Parameter Store standard tier (always free); no Secrets Manager | ⏳ Pending |
| 4.2.6 | Frontend on S3 + CloudFront | Build React app; upload to S3; CloudFront distribution; cache invalidation on deploy | ⏳ Pending |
| 4.2.7 | CodePipeline + CodeBuild | Source (GitHub) → build (tests + image + ECR push) → deploy (Lambda/EB + S3 sync + CloudFront invalidation); stay within 100 free build minutes/month | ⏳ Pending |
| 4.2.8 | Update Sentry release tagging | Tag releases using CodeBuild build ID / image tag to maintain error → deployment traceability | ⏳ Pending |
| 4.2.9 | Update canary monitoring | Point `API_BASE_URL` at new AWS backend URL; update UptimeRobot to monitor new endpoint | ⏳ Pending |
| 4.2.10 | Cut-over and smoke test | End-to-end smoke test on AWS URLs; confirm Sentry + notifications; decommission Render + Vercel | ⏳ Pending |

---

## Nice to Have — Monitoring
- [ ] Enhance `check_provider_status` to include account-level delivery logs (Resend `GET /emails`, Twilio `GET /Messages.json`) via `include_logs: bool = False`
- [ ] Add 4xx alerting thresholds (429, 404, 422, 401/403) as separate tracked metrics — currently visible in `query_request_logs` but do not trigger alerts

## Nice to Have — Features
- [ ] Stripe payment integration
- [ ] Customer order status tracking page
- [ ] Real geocoding for delivery radius (upgrade from zip code list)
- [ ] Admin panel API endpoints (once Lovable UI is ready)
- [ ] Upgrade Render to paid tier if cold starts become a problem
