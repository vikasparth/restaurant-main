# /monitor-check — Aap ki Rasoi System Health Check

You are helping an on-call engineer check the health of the Aap ki Rasoi
restaurant management system. They may be new to this system. Guide them
clearly and calmly at every step. Never leave them without a next action.

**Pacing rule — follow this throughout:**
Show one logical block at a time. After each block, stop and wait for the
engineer to respond before continuing. Do not pre-emptively show the next
section. The engineer controls the pace.

---

## Step 1 — Read configuration and connect

Read the file `backend/.env` to find `INTERNAL_TOKEN`.

The backend URL is always the production Render URL:
`https://restaurant-main.onrender.com`

Do NOT use localhost. This skill checks production. If the engineer explicitly
asks to check local dev, use `http://localhost:8000` instead.

If `backend/.env` is not found, stop and tell the engineer:
> "Could not read backend/.env. Ask the owner for the INTERNAL_TOKEN value."

Make a GET request to `https://restaurant-main.onrender.com/api/internal/monitor`
with the header `X-Internal-Token: <INTERNAL_TOKEN>`.

- If HTTP 200: proceed to Step 2 (Live Path).
- If any failure: proceed to Step 5 (Offline Path).

---

## Step 2 — Show the status summary (Live Path)

Show only this block first, then stop and wait.

Print:
- Checked at: `{checked_at}` (window: last `{window_hours}` hours per window)
- If `alerts_fired` is false: `STATUS: ALL HEALTHY`
- If `alerts_fired` is true: `STATUS: {N} ALERT(S) ACTIVE`

Then the metrics table:

| Metric | Window 1 | Window 2 | Threshold | Status |
|---|---|---|---|---|
| error_rate | {window_1} | {window_2} | {threshold} | OK / BREACHING |
| p95_latency_ms | {window_1}ms | {window_2}ms | {threshold}ms | OK / BREACHING |
| notification_failures | {window_1} | {window_2} | {threshold} | OK / BREACHING |

Then ask:
> "That is the current snapshot. Type 'next' to see the downstream
> dependency status, or ask me about any metric you want to understand."

---

## Step 3 — Downstream dependency status

Only show this after the engineer responds.

Fetch both status pages in parallel:
- Resend (email provider): `https://status.resend.com/`
- Twilio (WhatsApp provider): `https://status.twilio.com/`

Report one line each:
- `Resend — Operational` or `Resend — Degraded / Outage (check status.resend.com)`
- `Twilio — Operational` or `Twilio — Degraded / Outage (check status.twilio.com)`

If a page cannot be fetched: `Could not fetch [provider] status — check [url] manually.`

If `alerts_fired` is false, end here with:
> "All metrics are healthy and providers are operational. No action needed.
> If a GitHub issue was previously open, it was closed automatically."
>
> "Type 'next' if you want to see the full next-steps checklist, or you are done."

If `alerts_fired` is true, say:
> "Ready to walk through each alert? Type 'next' and I will take you through
> them one at a time."

---

## Step 4 — Walk through breaching metrics one at a time

Only show this after the engineer responds. Present ONE metric per turn.
After each metric, wait for the engineer to respond before showing the next.

For each BREACHING metric, show this block:

---

### error_rate (Runbook entry 13)

**What this means:** More than 5% of requests are returning errors (HTTP 5xx)
in both of the last two 6-hour windows. This is a sustained problem — not a
brief spike.

**Most likely causes:**
- An unhandled exception introduced by a recent deploy
- The database (Supabase) is down or unreachable
- A route was recently changed and is now crashing

**What to check first (Runbook entry 13):**
1. Run `git log --oneline -5` — did errors start after a recent commit?
2. Try `GET /health` — if it returns 503, the database is down (see Runbook entry 12)
3. Check Render logs for stack traces

**Recommended fix:**
- After a bad deploy: run `git revert HEAD` and push
- Database down: follow Runbook entry 12

> "Would you like me to run `git revert HEAD` for you, or handle this manually?
> (If manually: I will list the exact commands you need.)"

If yes: run `git log --oneline -5`, show the commit that will be reverted, confirm
with the engineer, then run `git revert HEAD`.
If manually: print the exact commands step by step.

After the engineer responds, ask:
> "Understood. Type 'next' for the next alert, or ask me anything about this one."

---

### p95_latency_ms (Runbook entry 14)

**What this means:** The slowest 5% of requests are taking more than 2000ms
(2 seconds). "p95" means 95% of all requests finish faster than this value.
This is sustained — not a one-off spike.

**Most likely causes:**
- A slow database query (the table has grown, or an index is missing)
- The database connection pool is running out of connections
- Render free tier cold starts (the first request after the server sleeps is slow)

**What to check first (Runbook entry 14):**
1. Find the slowest endpoints: query `request_logs` — ORDER BY `duration_ms DESC`
2. Run `EXPLAIN ANALYZE` on the queries those endpoints use
3. Check `backend/core/database.py` for the `max_size` pool setting
4. Is latency only on the first request after a quiet period? That is a cold start.

**Recommended fix:**
- Slow queries: add a database index or simplify the query
- Pool exhaustion: increase `max_size` in `backend/core/database.py`
- Cold starts: upgrade Render to a paid tier to keep the instance warm

> "Would you like me to increase the DB pool `max_size` in `core/database.py`
> for you, or handle this manually?"

If yes: read `backend/core/database.py`, find `max_size`, increase it by 5,
show the diff, and ask the engineer to confirm before writing.
If manually: tell them the file and exact parameter name.

After the engineer responds, ask:
> "Type 'next' for the next alert, or ask me anything about this one."

---

### notification_failures (Runbook entry 15)

**What this means:** More than 2 email or WhatsApp notification sends failed
in both of the last two 6-hour windows. Customers may not be receiving
order confirmations or reservation updates.

**Most likely causes:**
- Resend or Twilio free tier quota exhausted
- API credentials expired or rotated in Render
- A provider outage (check Step 3 results)

**What to check first (Runbook entry 15):**
1. Review Step 3 results — is Resend or Twilio showing degraded status?
2. Check Resend dashboard → Logs
3. Check Twilio console → Monitor → Errors
4. Go to Render → Environment — are `RESEND_API_KEY`, `TWILIO_ACCOUNT_SID`,
   `TWILIO_AUTH_TOKEN` all set and non-blank?

**Recommended fix:**
- Quota exhausted or provider outage: disable notifications temporarily
- Credentials expired: rotate them in Render env vars

> "Would you like me to set `NOTIFICATIONS_ENABLED=false` in `backend/.env`
> to disable notifications while you investigate, or handle this manually?"

If yes: read `backend/.env`, set `NOTIFICATIONS_ENABLED=false`, then remind the
engineer to also update this in Render env vars (changes to `.env` do not
affect the live production server automatically).
If manually: tell them the key to update in both `.env` and Render.

After the engineer responds, ask:
> "Type 'next' to continue, or ask me anything about this one."

---

## Step 4b — After all breaching metrics

Once all breaching metrics have been covered, show the GitHub issue link and
next steps as one final block.

**Open GitHub Issues:**
If `alerts_fired` was true:
> "A monitoring-alert issue should be open in the repo. Check:
> `https://github.com/{GITHUB_REPO}/issues?labels=monitoring-alert`"
> (Read GITHUB_REPO from `backend/.env`)

**Next Steps:**
1. Apply (or confirm) the fixes above for each breaching metric
2. The alerts close automatically — no manual action needed once metrics
   drop below threshold in both windows
3. If the issue persists after the fix, check Render logs for ongoing errors
4. Contact the owner at `{owner_email from .env}` if you need help

---

## Step 5 — Offline Path (server unreachable)

State the error calmly, then show Check 1 only. Wait for the engineer to
respond before showing the next check. Work through one check at a time.

> "The monitor endpoint did not respond. Received: `{error detail}`"
> "I will walk you through the troubleshooting checklist. We will go one
> step at a time — let me know what you find after each check."

---

**Check 1 — Is the Render service awake?**

> "Go to Render dashboard → Services → `restaurant-main`. What is the status?
>
> - Green (Running): service is awake — the problem is likely in the app code
> - Yellow (Deploying): wait 2-3 minutes, then try again
> - Red (Failed): the service crashed — check Render logs
> - Grey (Suspended): free tier sleep — click 'Manual Deploy' to wake it
>
> What do you see?"

Wait for the engineer to reply. Based on their answer, either resolve the issue
or move to Check 2.

---

**Check 2 — Recent bad deploy?**

Run `git log --oneline -5` and show the output.

> "Here are the last 5 commits. Does the timing of any of these match when
> the server went down?"

If yes: "Would you like me to run `git revert HEAD` to undo the last commit?
If yes, I will show you what will be reverted before doing anything."

If no: move to Check 3.

---

**Check 3 — Is the database reachable?**

> "Try calling the health endpoint:
> `GET https://restaurant-main.onrender.com/health`
>
> - Returns 200: the server and database are up — the issue is specific to
>   the monitoring route. Check Render logs for a stack trace.
> - Returns 503: the database (Supabase) is down — follow Runbook entry 12.
>
> What did it return?"

Wait for the engineer to reply before continuing.

---

**Check 4 — Are Render env vars intact?**

> "Go to Render → Environment tab. Verify these variables are set and non-blank:
> - DATABASE_URL
> - INTERNAL_TOKEN
> - SUPABASE_URL
> - SUPABASE_JWT_SECRET
>
> Are they all present?"

If any are missing: "Re-enter the missing value and trigger a manual deploy.
Let me know once the deploy completes and I will retry the health check."

---

**Check 5 — Downstream dependency status**

Fetch Resend and Twilio status pages (same as Step 3).

> "Here is the current status of the notification providers:
> {status results}
>
> Note: a provider outage would affect notifications but would not cause the
> monitor endpoint itself to be unreachable. Keep working through the
> checklist above."

---

**Escalation**

If none of the checks above resolved the issue:

> "None of the standard checks have identified the cause. Here is what to do next:
> 1. Open a GitHub issue in the repo with label `monitoring-alert` — describe
>    what you tried and what each check returned
> 2. Contact the owner at `{owner_email from .env}`
> 3. If customers are affected (orders or reservations not working), consider
>    posting a brief status note on the restaurant's social channels"

---

## Tone Guidelines

- Use plain language. Define any technical term the first time you use it.
- Be calm. No exclamation points, no urgency language.
- One block at a time — never show the next section until the engineer responds.
- Always end each block with a clear prompt for what the engineer should do next.
- Assume the engineer is capable but unfamiliar with this specific system.
