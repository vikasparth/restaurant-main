# Spec — Task 3.12: `/monitor-check` Claude Code Skill

## What it is

A Claude Code skill at `.claude/skills/monitor-check/SKILL.md`.  
Invoked by typing `/monitor-check` in the IDE.  
No backend changes. No new tests. No migrations.

---

## Primary Persona

A new on-call engineer — possibly their first shift, possibly 2am, possibly the
first person besides the owner to ever look at this system. The skill must guide
them confidently regardless of system state.

---

## Two Operating Paths

| Path | Triggered when | What Claude does |
|---|---|---|
| **Live** | Endpoint returns HTTP 200 | Fetch metrics → display table → interpret → recommend fix → offer to apply |
| **Offline** | Endpoint unreachable / non-200 | Structured guided troubleshooting — never dead-ends |

---

## Live Path — Step by Step

1. Read `.env` to find `INTERNAL_TOKEN` and determine backend URL  
   (default: `http://localhost:8000`; if `ENVIRONMENT=production` use the Render URL from `.env`)
2. `GET /api/internal/monitor` with header `X-Internal-Token: <token>`
3. Print **Status Summary**: `ALL HEALTHY` or `N ALERTS ACTIVE`
4. Print **Metrics Table** — one row per metric:

   | Metric | Window 1 | Window 2 | Threshold | Status |
   |---|---|---|---|---|
   | error_rate | ... | ... | 5% | OK / BREACHING |
   | p95_latency_ms | ... | ... | 2000ms | OK / BREACHING |
   | notification_failures | ... | ... | 2 | OK / BREACHING |

5. **Downstream Dependency Health** — fetch public status pages:
   - Resend: `https://status.resend.com/`
   - Twilio: `https://status.twilio.com/`
   - Report: Operational / Degraded / Outage for each

6. For each **breaching** metric:
   - Plain-language explanation of what the metric means (no jargon without explanation)
   - Most likely causes (from runbook)
   - Diagnostic steps — cite exact runbook entry (13 = error_rate, 14 = p95_latency_ms, 15 = notification_failures)
   - Recommended fix — specific command or file edit
   - **Offer:** "Would you like me to apply this fix now, or handle it manually?"
     - If apply: execute the fix (run the command, edit the file)
     - If manual: list the exact steps

7. Print **Open GitHub Issues** — check if a `monitoring-alert` issue is already open; link to it if so

8. End with **Next Steps** — numbered, calm, specific

---

## Offline Path — Step by Step

Triggered when: endpoint times out, returns 4xx/5xx, or connection refused.

1. State the error clearly: "Server did not respond (received: `<error>`)"
2. Work through this checklist in order:

   **Check 1 — Is Render awake?**
   - Go to Render dashboard → Services → check status
   - If sleeping: click Manual Deploy or wait for warm-up
   
   **Check 2 — Recent bad deploy?**
   - Run: `git log --oneline -5`
   - If deploy coincides with alert: `git revert HEAD` then push

   **Check 3 — Is the database reachable?**
   - Try: `GET /health` — if 503, see runbook entry 12

   **Check 4 — Are Render env vars intact?**
   - Required: `DATABASE_URL`, `INTERNAL_TOKEN`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`
   - Go to Render → Environment → verify all are set

   **Check 5 — Downstream dependencies**
   - Fetch Resend status: `https://status.resend.com/`
   - Fetch Twilio status: `https://status.twilio.com/`

3. **Escalation path** (if nothing resolves it):
   - Open a GitHub Issue manually with label `monitoring-alert`
   - Notify owner at the email in `settings.owner_email`

---

## Output Style Rules

- Plain language — define jargon on first use (e.g. "p95 latency means 95% of requests completed faster than this value")
- Calm tone — no exclamation points, no urgency language
- Always actionable — every section ends with a clear next step
- Never leave the engineer without a path forward
- Runbook entry cited by number for every alert

---

## Fix Offer Scope

| Metric / Scenario | Can skill apply fix? | What it does |
|---|---|---|
| error_rate after bad deploy | Yes | Generates `git revert` command |
| error_rate DB down | Partial | Opens runbook entry 12 steps |
| p95 slow queries | Partial | Suggests `EXPLAIN ANALYZE` SQL to run |
| p95 pool exhaustion | Yes | Edits `core/database.py` max_size |
| notification_failures quota | Yes | Edits `.env` to set `NOTIFICATIONS_ENABLED=false` |
| notification_failures credentials | Partial | Lists the Render env var to update |

---

## File to Create

`.claude/skills/monitor-check/SKILL.md`

---

## Out of Scope

- No backend changes
- No new tests
- No migrations
- Task 3.13 (MCP tools for deeper investigation) is a separate slice
