# Runbook — Aap ki Rasoi

> This runbook is a living document. Each entry maps to a monitored metric.
> Add a new entry whenever a new metric is instrumented in the monitoring agent.
> Last updated: 2026-04-14

---

## How to use this runbook

1. Receive an alert (WhatsApp / email / GitHub Actions failure)
2. Find the matching entry below by metric name
3. Follow Diagnostic Steps in order — stop when you find the cause
4. Apply the Fix
5. Verify the metric returns to normal after the fix

---

## 1. Memory Utilization — Upward Trend

**Symptom:** Memory usage on Render is trending upward over hours or days, not returning to baseline after requests complete.

**Likely cause:**
- Memory leak in the app (objects not being released)
- asyncpg connection pool connections not being returned
- Large query results loaded fully into memory

**Diagnostic steps:**
1. Check Render dashboard → Metrics → Memory graph — confirm the upward trend
2. Check if the trend started after a recent deploy (`git log --oneline -10`)
3. Check DB pool usage — are connections being held open?

**Fix:**
- If after a deploy: roll back and investigate the change
- If DB pool: restart the Render service (clears in-memory state), then investigate pool leak
- If persistent: upgrade Render instance memory tier temporarily while fixing the root cause

---

## 2. CPU Utilization — Upward or Spiky Trend

**Symptom:** CPU usage on Render is consistently high or showing frequent spikes.

**Likely cause:**
- Expensive DB queries running on every request
- Tight loops or synchronous blocking code on the async event loop
- Unusual spike in traffic (bot or abuse)

**Diagnostic steps:**
1. Check Render dashboard → Metrics → CPU graph — confirm spike timing
2. Correlate spike timing with request volume (check DB request log table)
3. Check for 429 rate limit hits — if none, traffic may be bypassing rate limits

**Fix:**
- If expensive queries: add DB indexes or cache results
- If blocking code: identify and move to a background task
- If abuse: check IP patterns, tighten rate limits

---

## 3a. Throttling — Inbound (Users hitting our rate limits)

**Symptom:** Rising number of 429 responses returned to users.

**Likely cause:**
- Single user or bot repeatedly hitting an endpoint
- Frontend bug causing rapid repeated API calls
- Legitimate user on slow connection retrying aggressively

**Diagnostic steps:**
1. Query request log table for 429s — group by IP and endpoint
2. Check if it's one IP or many (one = bot/bug, many = misconfigured frontend)
3. Check frontend for any retry logic without backoff

**Fix:**
- If single IP: investigate and consider IP block if abusive
- If frontend bug: fix retry logic, add exponential backoff
- If rate limit too tight: increase limit for the affected endpoint

---

## 3b. Throttling — Outbound (Downstream services throttling us)

**Symptom:** Notification failures increasing; Twilio or Resend returning 429 errors.

**Likely cause:**
- Free tier quota exhausted (Twilio: 50 WhatsApp messages/day sandbox limit)
- Burst of orders/reservations triggering too many notifications at once
- Credentials expired or account suspended

**Diagnostic steps:**
1. Check notification failure logs in DB
2. Log in to Twilio/Resend dashboard — check quota usage and account status
3. Check if failures are consistent (quota) or intermittent (credentials)

**Fix:**
- If Twilio sandbox quota: wait until midnight UTC for reset, or upgrade to paid
- If Resend quota: check free tier limits, upgrade if needed
- Set `NOTIFICATIONS_ENABLED=false` in Render env vars to stop further failures while investigating

---

## 4. Latency — Upward Trend

**Symptom:** API response times are trending upward; requests taking longer than usual.

**Likely cause:**
- DB query performance degrading (missing index, table growth)
- DB connection pool nearing capacity
- Render cold starts (service went to sleep on free tier)

**Diagnostic steps:**
1. Check latency middleware logs — which endpoints are slowest?
2. Check DB pool usage — connections near max_size?
3. Check if latency is consistent (DB issue) or occasional spikes (cold starts)

**Fix:**
- If DB queries: run `EXPLAIN ANALYZE` on slow queries, add indexes
- If pool exhaustion: increase `max_size` in `core/database.py`
- If cold starts: upgrade Render to paid tier to keep instance warm

---

## 5. 4xx Error Rate — Increasing

**Symptom:** Rising volume of 4xx responses (400, 404, 422, 429).

**Likely cause:**
- 422 spike after a deploy = Pydantic model mismatch (frontend sending wrong field names)
- 404 spike = frontend calling an endpoint that no longer exists
- 429 spike = rate limiting being hit (see entry 3a)

**Diagnostic steps:**
1. Query request log table — group 4xx errors by status code and endpoint
2. Check if spike started after a recent deploy
3. For 422s: compare request payload in logs against current Pydantic model

**Fix:**
- If 422 after deploy: roll back deploy, fix model mismatch, redeploy
- If 404: check if endpoint was renamed or removed, update frontend

---

## 6. 5xx Error Rate — Any Spike

**Symptom:** Any 5xx responses (500, 503) appearing in logs.

**Likely cause:**
- Unhandled exception in a route handler
- DB connection lost or pool exhausted
- Render service crashed and restarted

**Diagnostic steps:**
1. Check Render logs for stack traces — identify the failing endpoint
2. Check DB health — is `/health` returning 503?
3. Check if the error is consistent or intermittent

**Fix:**
- If DB down: check Supabase dashboard for outages
- If unhandled exception: fix the bug and deploy
- If Render crash: check Render logs for OOM or process exit reason

---

## 7. Page Crash Errors (Frontend)

**Symptom:** Sentry reports a React error boundary firing; users see a blank page or error screen.

**Likely cause:**
- Unhandled null/undefined in a component (e.g. API returned unexpected shape)
- A recent frontend deploy introduced a breaking change

**Diagnostic steps:**
1. Open Sentry → Issues — find the error, check stack trace and affected component
2. Check if the crash started after a recent Vercel deploy
3. Reproduce locally with `npm run dev`

**Fix:**
- If after deploy: roll back Vercel deployment
- If null/undefined: add a guard clause or optional chaining in the component

---

## 8. JS Error Rate — New Unique Error Type

**Symptom:** Sentry reports a new error type that wasn't present in the previous 24 hours.

**Likely cause:**
- Code change introduced a JS exception on a specific user action
- Third-party library update broke something
- Browser compatibility issue

**Diagnostic steps:**
1. Open Sentry → Issues — filter by "First seen: last 24h"
2. Check the stack trace — identify the file and line number
3. Check if it's reproducible in the browser dev console

**Fix:**
- Fix the specific code path and deploy
- If third-party library: pin to previous version until fix is available

---

## 9. Network Error Rate — Failed API Calls

**Symptom:** Sentry reports fetch() failures to `/api/*` endpoints from the browser.

**Likely cause:**
- Backend is down (correlate with `/health` status)
- CORS misconfiguration after a deploy
- Vercel rewrite broken (vercel.json changed)

**Diagnostic steps:**
1. Check if `/health` is returning 200 — if not, backend issue (see entries 6, 11)
2. Check browser dev tools Network tab — what is the exact error?
3. Check `vercel.json` — is the rewrite still pointing to the correct Render URL?

**Fix:**
- If backend down: follow entry 6 or 11
- If CORS: check `ALLOWED_ORIGINS` env var on Render
- If Vercel rewrite: fix `vercel.json` and redeploy

---

## 10. Unusual Request Counts

**Symptom:** Sudden spike or drop in request volume vs. normal pattern.

**Likely cause:**
- Spike: bot traffic or abuse
- Drop during peak hours (12–2pm, 6–9pm): checkout flow broken (see entries 6, 9)
- Drop at all times: Vercel/Render deployment issue

**Diagnostic steps:**
1. Check request log table — is the drop on all endpoints or one specific endpoint?
2. If spike: check IPs — is it concentrated on one IP?
3. If drop during peak: manually test the order flow on the live site

**Fix:**
- If bot spike: tighten rate limits, consider IP block
- If checkout broken: follow entry 6 or 9
- If deployment issue: check Vercel and Render dashboards

---

## 11. Availability Drop

**Symptom:** UptimeRobot alerts `/health` is down; canary tests failing.

**Likely cause:**
- Render service crashed or is restarting
- Supabase DB is down
- Render free tier instance went to sleep (cold start taking >30s)

**Diagnostic steps:**
1. Open `https://restaurant-main.onrender.com/health` in browser
2. Check Render dashboard — is the service running?
3. Check Supabase dashboard — is the DB reachable?
4. Check GitHub Actions canary results for which test failed

**Fix:**
- If Render crashed: check logs for crash reason, restart service
- If Supabase down: wait for Supabase incident resolution (check status.supabase.com)
- If cold start: upgrade Render to paid tier to prevent sleep

---

## 12. Downstream Dependency Failures

**Symptom:** Errors from Twilio, Resend, or Supabase logged in the DB.

**Likely cause:**
- Service outage at the provider
- API credentials expired or rotated
- Free tier quota exhausted

**Diagnostic steps:**
1. Check the provider's status page:
   - Twilio: status.twilio.com
   - Resend: resend.com/status (or check their dashboard)
   - Supabase: status.supabase.com
2. Check Render env vars — are credentials still set correctly?
3. Check notification failure logs — is it consistent or intermittent?

**Fix:**
- If provider outage: wait for resolution, set `NOTIFICATIONS_ENABLED=false` temporarily
- If credentials expired: rotate and update in Render env vars
- If quota: upgrade provider plan or disable feature temporarily
