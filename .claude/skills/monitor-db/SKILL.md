# monitor-db — Database Health and Performance Checks

You are investigating the **database layer** of the Aap ki Rasoi system.
Your job is to determine whether the database is the root cause of the
current alert — either through being unreachable, pool exhaustion, or
slow queries.

Work through the checks below one at a time. After each check, report
what you found before moving on.

---

## Check 1 — Is the database reachable?

Call MCP tool `check_health_endpoint()` and report the result:
- **reachable**: database is reachable — move to Check 2
- **unreachable**: database (Supabase) is down — tell the engineer:
  > "The database is not reachable. Follow runbook entry 12
  > (backend/docs/runbook.md — Downstream Dependency Failures) for next steps.
  > Check the Supabase dashboard at supabase.com for outage status."
  Stop here — do not proceed to Check 2.

---

## Check 2 — Slow query analysis

Call MCP tool `query_request_logs(window_hours=12)` and show the results as a table.

If any endpoint has avg_ms > 1000:
> "These endpoints are consistently slow. The queries they run likely
> need an index or optimisation."

Read `backend/docs/runbook/p95_latency_ms.md` and show the slow query fix steps.

---

## Check 3 — Connection pool assessment

Read `backend/core/database.py` and find the `max_size` parameter.
Report the current value.

Then read `backend/docs/runbook/p95_latency_ms.md` — the pool exhaustion section
has the decision rule for when (and whether) to increase `max_size`, including
the Supabase connection limit constraint.

Present the relevant fix steps from the runbook and ask:
> "Would you like me to apply the pool change, or handle it manually?"

If yes: show the diff, wait for confirmation, then apply the edit.

---

## Check 4 — Cold start test

**Only run this check if Check 2 showed no slow queries and Check 3 ruled out
pool exhaustion.**

Ask:
> "Is the high latency consistent throughout the day, or only on the
> first request after a quiet period (e.g. first request each morning)?"

If only on first request:
> "This is a Render free tier cold start. The server sleeps after 15
> minutes of inactivity and the first request pays a warm-up cost."
Read `backend/docs/runbook/p95_latency_ms.md` and show the cold start fix steps.

---

## Check 5 — Render logs (fallback)

**Only run this check if Checks 2, 3, and 4 all found no root cause.**

Do not ask the engineer to check the Render dashboard manually.

**Before calling `get_render_logs()`:** check if Render logs are already in
context from this session (look for "Render logs (fetched at ...)"). If yes,
use those. If no, call `get_render_logs(lines=100)` now and note the result
as "Render logs (fetched at monitor-db Check 5)".

Scan for:
- `Exception`, `Error`, `Traceback`
- Repeated timeouts or connection reset messages
- Any pattern correlating with the latency window

If suspicious lines found: identify the pattern and suggest the fix.

If nothing found:
> "DB layer checks are exhausted — no slow queries, pool is within limits,
> not a cold start pattern, and Render logs are clean. This may be an
> infrastructure issue outside the application. Check Supabase and Render
> dashboards directly."

---

## Reporting back

End with a clear finding statement for the orchestrator synthesis step:

> "DB layer finding: [database reachable / database unreachable /
> pool at max_size X — likely exhausted / slow queries on endpoints X, Y /
> cold start pattern detected]"
