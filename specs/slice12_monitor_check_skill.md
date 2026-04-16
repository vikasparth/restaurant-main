# Spec — Task 3.12: `/monitor-check` Claude Code Skill (v2)

> Supersedes the original spec. Updated after architecture review to use
> layered sub-skills, structured per-metric runbook files, and a synthesis step.
> See ADR-0008 for the design rationale.

---

## What it is

A set of Claude Code skill files that together form a guided on-call health
check for the Aap ki Rasoi restaurant management system.

No backend changes. No new tests. No migrations.

---

## Primary Persona

A new on-call engineer — possibly their first shift, possibly 2am. The skill
must guide them confidently regardless of system state. One block at a time.
Never leave them without a next action.

---

## File Structure

```
.claude/skills/
    monitor-check/SKILL.md          ← orchestrator (~85 lines)
    monitor-web/SKILL.md            ← Render + deploy checks (~65 lines)
    monitor-db/SKILL.md             ← DB health + pool + slow query checks (~60 lines)
    monitor-dependencies/SKILL.md   ← Resend + Twilio status checks (~45 lines)

docs/runbook/
    index.md                        ← human index, replaces the flat runbook sections
    error_rate.md                   ← metric context, root causes, fix steps
    p95_latency_ms.md
    notification_failures.md
    (existing entries migrate from docs/runbook.md incrementally)
```

---

## Responsibility Boundaries — No Overlap

| Layer | Knows | Does NOT contain |
|---|---|---|
| Orchestrator | Routing table (metric → sub-skill sequence), synthesis step | Diagnostics, fix details |
| Sub-skills | How to investigate a layer (commands, checks, what to look for) | What the metric means, fix steps |
| Runbook files | Metric context, root causes, fix steps, thresholds | How to run commands |

---

## Orchestrator — `/monitor-check`

**Step 1 — Read config and call production endpoint**
- Read `backend/.env` for `INTERNAL_TOKEN`
- Always call `https://restaurant-main.onrender.com/api/internal/monitor`
- HTTP 200 → Live Path; any failure → Offline Path

**Step 2 — Show status summary and metrics table**
- STATUS: ALL HEALTHY / N ALERT(S) ACTIVE
- Metrics table: metric, window_1, window_2, threshold, OK/BREACHING
- Stop and wait for engineer to respond

**Step 3 — Route to sub-skills based on findings**

Routing table:

| Trigger | Sub-skill sequence |
|---|---|
| `error_rate` breaching | monitor-web → monitor-db |
| `p95_latency_ms` breaching | monitor-db only |
| `notification_failures` breaching | monitor-dependencies only |
| Server unreachable | monitor-web → monitor-db → monitor-dependencies |
| All healthy | Skip sub-skills — go to Step 5 (downstream status only) |

Work through sub-skills one at a time. After each sub-skill completes, ask
the engineer to confirm before loading the next one.

**Step 4 — Synthesis (cross-layer analysis)**

After all relevant sub-skills have reported, hold all findings in view and:
- Look for timing correlations across layers (e.g. deploy time vs metric spike)
- Look for causal chains (e.g. connection leak → pool exhaustion → error rate up)
- Look for a single root cause spanning multiple layers
- State the conclusion plainly before recommending any fix

**Step 5 — Downstream dependency status**

Load `monitor-dependencies` sub-skill if not already loaded.
If all healthy: close with summary and next steps.
If alerts fired: include GitHub issue link and next steps.

**Pacing rule (applies throughout):**
One block at a time. Stop after each block and wait for the engineer to respond.
The engineer controls the pace.

---

## Sub-skill: `monitor-web`

Investigates the Render service and recent deploys. Called when `error_rate`
breaches or server is unreachable.

Checks (in order):
1. Is the Render service awake? (guide engineer to dashboard — status indicators)
2. Recent bad deploy? — run `git log --oneline -5`, ask if timing matches
3. Offer `git revert HEAD` if confirmed bad deploy

After each check: report finding clearly, ask what the engineer sees before
moving to the next check.

When root cause found: read `docs/runbook/error_rate.md` for fix details.
Offer to apply the fix or list manual steps.

---

## Sub-skill: `monitor-db`

Investigates database health, connection pool, and slow queries. Called when
`error_rate` or `p95_latency_ms` breaches.

Checks (in order):
1. Is the database reachable? — call `GET /health`, interpret 200 vs 503
2. Connection pool — check `backend/core/database.py` for `max_size`
3. Slow queries — query `request_logs` ORDER BY `duration_ms DESC`
4. Cold start test — is latency only on the first request after a quiet period?

When root cause found: read the relevant runbook file for fix details.
- `p95_latency_ms` breach → `docs/runbook/p95_latency_ms.md`
- `error_rate` breach (DB cause) → `docs/runbook/error_rate.md`

Offer to apply fix (e.g. increase `max_size`) or list manual steps.

---

## Sub-skill: `monitor-dependencies`

Investigates Resend and Twilio. Called when `notification_failures` breaches
or as the final check in the offline path.

Checks (in order):
1. Fetch `https://resend-status.com/` — Operational / Degraded / Outage
2. Fetch `https://status.twilio.com/` — Operational / Degraded / Outage
3. Query `notification_logs` for recent failures — provider, error_code
4. Guide engineer to check Render env vars for `RESEND_API_KEY`, `TWILIO_AUTH_TOKEN`

When root cause found: read `docs/runbook/notification_failures.md` for fix details.
Offer to set `NOTIFICATIONS_ENABLED=false` in `.env` or list manual steps.

Note: always remind engineer that `.env` changes do not affect the live
production server — Render env vars must be updated separately.

---

## Runbook File Format (per-metric)

Each file in `docs/runbook/` follows this structure so sub-skills can read
and present it directly without reformatting:

```markdown
# [Metric Name] — Runbook Entry [N]

**Threshold:** [value]
**Alert fires when:** [condition — both windows explanation]

## What this means
[Plain-language explanation, no jargon]

## Most likely causes
- [cause 1]
- [cause 2]
- [cause 3]

## Fix steps
### [Fix scenario 1]
[Exact steps]

### [Fix scenario 2]
[Exact steps]

## Alert auto-closes when
[condition]
```

---

## MCP Bridge (Task 3.13)

Each sub-skill maps to one or more MCP tools. The orchestrator routing table
does not change — only the sub-skills swap file reads for tool calls:

| Today (sub-skill reads/asks) | 3.13 (MCP tool call) |
|---|---|
| `GET /health` (Step 1) | `check_health_endpoint()` |
| `git log --oneline -5` | `get_recent_commits()` |
| Engineer pastes Render logs manually | `get_render_logs(lines=100)` — removes manual step |
| Query `request_logs` | `query_metrics_table(metric, window)` |
| Fetch status pages | `check_provider_status(provider)` |
| Read runbook file | `get_runbook_entry(metric)` |

**`get_render_logs` is the key 3.13 upgrade:** once available, Render log health
becomes part of the automatic summary in Step 2 — no manual copy-paste needed.
The `monitor-web` Check 3 instruction switches from "ask engineer to paste logs"
to "call get_render_logs() and analyse automatically".

The synthesis step remains identical — Claude holds all tool results in context
and reasons across them.

---

## Out of Scope for This Task

- Splitting `docs/runbook.md` into per-file format — incremental, done alongside
  each new metric added (not a big-bang migration)
- MCP tool implementation — task 3.13
- No backend changes, no tests, no migrations
