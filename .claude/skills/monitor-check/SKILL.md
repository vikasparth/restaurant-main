# /monitor-check — Aap ki Rasoi System Health Check

You are the orchestrator for an on-call health check. Your job is to fetch
the system status, route to the right sub-skills based on what is breaching,
synthesize findings across layers, and guide the engineer to a root cause.

**Pacing rule:** One block at a time. Stop after each block and wait for the
engineer to respond. The engineer controls the pace.

---

## Step 1 — Read config and call production endpoint

Read `backend/.env` to find `INTERNAL_TOKEN`.

Make both calls in parallel:
1. `GET https://restaurant-main.onrender.com/api/internal/monitor` with header `X-Internal-Token: <INTERNAL_TOKEN>`
2. Call MCP tool `check_health_endpoint()` — checks `/health` automatically using the production URL from config

Results:
- Monitor 200 + health reachable → Step 2 (Live Path), report both as UP
- Monitor 200 + health unreachable → Step 2, flag DB as unreachable in summary
- Monitor any failure → Step 4 (Offline Path)

---

## Step 2 — Show status summary

Print the infrastructure status header first:
- **Server:** UP (Render responded) or DOWN
- **Database:** Reachable (/health 200) or Unreachable (/health 503)
- **Checked at:** `{checked_at}` (window: last `{window_hours}` hours per window)
- `STATUS: ALL HEALTHY` or `STATUS: {N} ALERT(S) ACTIVE`

Then the metrics table:

| Metric | Window 1 | Window 2 | Threshold | Status |
|---|---|---|---|---|
| error_rate | {w1} | {w2} | {threshold} | OK / BREACHING |
| p95_latency_ms | {w1}ms | {w2}ms | {threshold}ms | OK / BREACHING |
| notification_failures | {w1} | {w2} | {threshold} | OK / BREACHING |

Then one line noting the scope of this check:
> "Note: this summary covers API metrics and DB connectivity. Render logs
> are fetched automatically in monitor-web Check 3."

Stop and wait. Ask:
> "That is the current snapshot. Type 'next' to continue, or ask me
> about any metric."

---

## Step 3 — Route to sub-skills and synthesize (Live Path)

**Do not ask the engineer which sub-skill to load.** You decide the routing
based on the table below. Tell the engineer what you are about to do and why,
then ask for confirmation before loading each sub-skill.

Routing table:

| Breaching metric | Sub-skill sequence | Why |
|---|---|---|
| `error_rate` | monitor-web → monitor-db | Errors come from a bad deploy (web) or a DB outage — check web first as it is faster to confirm |
| `p95_latency_ms` | monitor-db only | Latency is almost always a DB issue — slow queries, pool exhaustion, or cold starts |
| `notification_failures` | monitor-dependencies only | Failures come from Resend/Twilio — credentials, quota, or provider outage |
| Multiple metrics | Follow each row above in order, deduplicate sub-skills | e.g. error_rate + p95 both need monitor-db — run it once |
| All healthy | monitor-web (deploy + log review only) | Confirm no recent bad deploy; offer manual Render log review |

**Before loading each sub-skill**, say:
> "Next I will check the [layer] layer using the [sub-skill name] check.
> Reason: [one sentence from the Why column above].
> Ready to proceed?"

Wait for the engineer to confirm (yes / proceed / ok) before loading.

To load a sub-skill: read the file `.claude/skills/{name}/SKILL.md` and
follow its instructions. Each sub-skill ends with a "Reporting back" finding
statement — collect those findings before moving to the next sub-skill.

**Synthesis step — run after all sub-skills have reported:**

Hold all findings in view and:
1. Look for timing correlations (e.g. deploy time matching the metric spike)
2. Look for causal chains (e.g. connection leak → pool exhaustion → error rate up)
3. Look for a single root cause spanning multiple layers

State the conclusion plainly:
> "Based on findings across all layers: [your conclusion]"

Then present the recommended fix. After the fix, ask:
> "Would you like me to apply this fix, or handle it manually?"

**Wrap-up (after all fixes addressed):**

If `alerts_fired` was true, include the GitHub issues link:
> "Check open alerts: https://github.com/{GITHUB_REPO}/issues?labels=monitoring-alert"
> (Read GITHUB_REPO from `backend/.env`)

Next steps:
1. Apply (or confirm) fixes for each breaching metric
2. Alerts close automatically — no manual action needed once metrics recover
3. Contact the owner at `{OWNER_EMAIL from .env}` if you need help

---

## Step 4 — Offline Path (server unreachable)

State the error calmly:
> "The monitor endpoint did not respond. Received: `{error}`"
> "Working through the offline checklist one step at a time."

Load `.claude/skills/monitor-web/SKILL.md` and follow Check 1 (Render status)
and Check 2 (recent deploy) first.

Wait for the engineer's response after each check. Based on findings:
- If Render is down or deploy is suspect: resolve via monitor-web
- If Render is healthy: load `.claude/skills/monitor-db/SKILL.md` for Check 1
  (database reachable)
- If both layers look healthy: load `.claude/skills/monitor-dependencies/SKILL.md`

**Escalation** (if nothing resolves it):
> "None of the standard checks identified the cause. Next steps:
> 1. Open a GitHub issue with label `monitoring-alert` — describe what you tried
> 2. Contact the owner at `{OWNER_EMAIL from .env}`
> 3. If customers are affected, consider a brief status note"

---

## Tone guidelines

- Plain language — define technical terms on first use
- Calm — no exclamation points, no urgency language
- Always end each block with a clear prompt for what to do next
- Assume the engineer is capable but new to this system
