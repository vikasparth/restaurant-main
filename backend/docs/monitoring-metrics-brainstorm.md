# Monitoring Metrics Brainstorm — Aap ki Rasoi

> Status: Draft — under review. This doc feeds into the AI monitoring agent slice (after 3.6).

---

## Goal

Move from reactive monitoring (UptimeRobot pings `/health`) to proactive intelligence — a scheduled Claude agent that reads signals, identifies anomalies, and alerts the owner with a recommended fix before customers are impacted.

---

## Category 1 — Availability

*Is the app alive?*

| Metric | Signal | Anomaly |
|---|---|---|
| `/health` HTTP status | 200 = healthy | Non-200 = outage |
| `/health` response time | Baseline ~200ms | >2s = Render cold start or DB slowness |

---

## Category 2 — Error Rates

*Is the app working correctly?*

| Metric | Signal | Anomaly |
|---|---|---|
| HTTP 5xx rate per endpoint | Should be ~0 | Spike = bug or DB issue |
| HTTP 422 rate on orders/reservations/catering | Should be ~0 in prod | Spike = frontend/model mismatch after a deploy |
| HTTP 429 rate | Should be ~0 | Spike = rate limit being hit, possible abuse |
| Notification failures (email/WhatsApp) | Logged per send | Rising count = Resend/Twilio quota approaching |

---

## Category 3 — Business Flow

*Are customers able to complete transactions?*

These are the most important signals — the app can be "healthy" while checkout is silently broken.

| Metric | Signal | Anomaly |
|---|---|---|
| Orders created per hour | Varies by time of day | Sudden drop during peak hours = checkout broken |
| Reservations created per hour | Varies by day | Drop during booking season = reservation flow broken |
| Catering enquiries per day | Low volume, 1–3/day | Zero for multiple days = catering form broken |
| Delivery zip validation requests | Tracks customer intent | Drop = delivery page not loading |

---

## Category 4 — Infrastructure

*Is the underlying platform healthy?*

| Metric | Signal | Anomaly |
|---|---|---|
| DB connection pool usage | Baseline 2–4 of 10 | >8/10 = slowdowns imminent, increase max_size |
| DB query latency (avg) | Baseline <50ms | Rising trend predicts timeouts before they happen |
| Render instance memory | Visible in Render dashboard | Approaching limit = memory leak |

---

## Category 5 — Restaurant-Specific Anomalies

*Patterns that only matter in the context of a restaurant business.*

| Pattern | What it might mean | Recommended action |
|---|---|---|
| Zero orders during lunch (12–2pm) or dinner (6–9pm) | Strong signal checkout is broken | Immediate investigation |
| Same customer email placing >5 orders in 1 hour | Bot or abuse | Flag for review, consider IP block |
| Orders placed between 2am–5am | Possible bot activity | Alert for review |
| Spike in 422s immediately after a deploy | Model mismatch introduced | Roll back deploy |
| Notification failure rate >20% in 1 hour | Resend/Twilio quota hit or credentials expired | Alert owner, disable notifications temporarily |

---

## Open Questions (to discuss)

1. **Where do we store metrics?** Options:
   - Supabase table (reuse existing DB, free)
   - Logflare (Render native log shipping, free tier)
   - In-memory counters exposed via `/api/internal/metrics` (simplest, but lost on restart)

2. **What is the right alert frequency?** Too noisy = ignored. Too quiet = missed issues.
   - Suggestion: alert only when confidence is high (e.g. 3 consecutive anomalies, not just 1)

3. **What time windows matter most?**
   - Lunch: 12pm–2pm
   - Dinner: 6pm–9pm
   - Should the agent know peak hours to weight anomalies differently?

4. **What is the Claude agent's output format?**
   - One-line summary + root cause hypothesis + recommended action
   - Example: *"Order rate dropped to 0 during dinner peak. Last successful order was 6:43pm. `/health` is green but `/api/orders` returned 503 twice in the last 10 min. Recommend: check Render logs for DB pool exhaustion."*

5. **Should the agent self-heal?** (e.g. auto-disable notifications when Twilio quota is hit)
   - Discuss scope — auto-healing adds complexity but reduces manual intervention

---

---

## Vikas's Proposed Metrics

Organised by where the data lives — this determines how we collect it.

### Backend / Infrastructure (readable from server or Render)

| # | Metric | Signal to watch | Data source |
|---|---|---|---|
| 1 | Memory utilization | Upward trend over time | Render dashboard / metrics API |
| 2 | CPU utilization | Upward or spiky trend | Render dashboard / metrics API |
| 3 | Throttling — inbound | Users hitting our rate limits (429s we return) | Our DB / request logs |
| 3b | Throttling — outbound | Twilio / Resend / Supabase returning 429 to us | Notification failure logs in DB |
| 4 | Latency | Upward trend in API response times | Middleware timing written to DB |
| 5 | 4xx error rate | Increasing volume (client or model errors) | Request log table in DB |
| 6 | 5xx error rate | Any spike (our bugs or DB issues) | Request log table in DB |
| 10 | Unusual request counts | Sudden spike or drop vs. normal pattern | Request log table in DB |
| 11 | Availability drop | `/health` non-200 or DB unreachable | UptimeRobot + health endpoint |
| 12 | Downstream dependency failures | Twilio, Resend, Supabase returning errors | Service call results logged to DB |

### Frontend (browser-side — needs client instrumentation)

| # | Metric | Signal to watch | Data source |
|---|---|---|---|
| 7 | Page crash errors | React error boundary fires | Sentry |
| 8 | JS error rate | New unique error types (not rate trend) | Sentry |
| 9 | Network error rate | Failed fetch() to `/api/*` endpoints only | Sentry |

> **Note on frontend metrics (7, 8, 9):** These cannot be measured from the backend — the backend never sees a page crash or a JS error. They require a client-side error tracking SDK. **Sentry** has a free tier and a React SDK that captures all three with ~5 lines of setup. This should be a separate small task before Phase 1 agent is built, otherwise the agent will have a blind spot on the frontend.

> **JS Error Rate — tracking approach:** This app has low traffic. A rate trend is not meaningful at this scale. What matters is a **new unique error type appearing** — especially on the checkout path (orders, reservations, catering). The Claude agent should alert when a new error type is seen that didn't exist in the previous 24h window, not when a percentage crosses a threshold.

> **Network Error Rate — scoping:** Browsers generate network errors for many reasons (bad connection, ad blockers, third-party scripts) — most are not actionable. Scope this metric to failed `fetch()` calls to our own `/api/*` endpoints only. A spike there means checkout is broken. Correlate with backend 5xx rate to distinguish "our API is down" from "model mismatch after a deploy".

### Cross-cutting observations

- **Throttling has two directions** — we rate-limit users (inbound) and our downstream providers rate-limit us (outbound). Both need separate tracking.
- **Latency requires middleware** — we need a FastAPI middleware that records request duration to a DB table. Not currently in place.
- **Render metrics API** — Render exposes CPU and memory via their API (requires Render API key). This gives Phase 1 something to read without scraping the dashboard.

---

## Agent Architecture — Phased Approach

### Guiding constraint
No additional Claude API cost. Owner has Claude Pro (covers Claude Code sessions). Scheduled backend calls to the Claude API are out of scope — they bill separately to the Anthropic API platform.

### Phase 1 — Rule-based monitoring (no LLM, zero additional cost)

```
cron fires → collect metrics snapshot → evaluate rules in Python → alert if anomaly found
```

- Pure Python threshold checks — no Claude API call
- Runs on existing Render instance (no new services, no new cost)
- Alerts via existing WhatsApp/email notification system
- Example rules:
  - order rate = 0 during 12–2pm or 6–9pm → alert
  - 5xx count > 5 in any 10-minute window → alert
  - memory utilisation > 85% → alert
  - downstream failure rate > 20% in 1 hour → alert
- **Cost: zero**

### Phase 2 — Claude Code Skill `/monitor-check` (on-demand, IDE-side)

```
owner types /monitor-check in IDE
  → Skill calls /api/internal/monitor (fetches latest metrics snapshot from DB)
  → passes snapshot to Claude (uses existing Claude Code session — covered by Claude Pro)
  → Claude analyses and displays result in terminal
```

- No scheduled Claude API calls — analysis only happens when owner explicitly triggers it
- Uses the Claude Code session, not a separate API billing account
- Built after Phase 1 backend endpoint exists
- **Cost: zero (covered by Claude Pro subscription)**

### Phase 3 — MCP server (future, optional)

```
/monitor-check → Claude calls MCP tools to investigate further
Claude calls tool: query_metrics_table(...)
Claude calls tool: check_endpoint(...)
Claude calls tool: get_recent_errors(...)
```

- Claude drives its own investigation during the Skill session
- MCP tools are Postgres queries against the metrics DB — no new external services
- Skill automatically gets richer output once MCP is in place without changes to the Skill itself
- **Cost: still zero (same Claude Code session)**
- **Log access note**: Render doesn't expose logs via API. Preferred approach: structured DB logging — app writes errors/events to `metrics_events` table, MCP tool is a Postgres query.

---

## Visualisation

For viewing metric patterns when notified: **Grafana Cloud** (free tier, connects to Supabase/Postgres natively). Suitable for time-series graphs and anomaly overlays. Metabase is an alternative for business-friendly reporting but less suited for live anomaly investigation.

---

## Runbook

A runbook (`docs/runbook.md`) will be created as part of task 3.8 and grown incrementally — one entry per monitored metric. Each entry covers: symptom, likely cause, diagnostic steps, fix. The runbook is updated alongside each metric as it is instrumented in the agent.

---

## Next Steps

- [x] Vikas shared metrics categories list — captured above
- [ ] Review and finalise metric categories (review this doc)
- [ ] Decide on metrics storage approach (Question 1 above — leaning Supabase table)
- [ ] Define alert thresholds per metric
- [ ] **3.6** — Canary monitoring setup
- [ ] **3.7** — Sentry setup (frontend error tracking pre-requisite)
- [ ] **3.8** — Runbook skeleton (`docs/runbook.md`)
- [ ] **3.9** — Request logging middleware (records endpoint, status code, duration to DB)
- [ ] **3.10** — Notification failure logging (records Twilio/Resend results to DB)
- [ ] **3.11** — Write spec and build Phase 1 monitoring agent (rule-based)
- [ ] **3.12** — Claude Code Skill `/monitor-check`
- [ ] **3.13** — Phase 2: MCP server
