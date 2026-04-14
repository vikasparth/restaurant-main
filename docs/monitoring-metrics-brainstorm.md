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

## Next Steps

- [ ] Review and finalise metric categories
- [ ] Decide on metrics storage approach (Question 1)
- [ ] Define alert thresholds per metric
- [ ] Write spec for AI monitoring agent slice
