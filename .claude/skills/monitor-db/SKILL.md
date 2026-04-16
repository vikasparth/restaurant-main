# monitor-db — Database Health and Performance Checks

You are investigating the **database layer** of the Aap ki Rasoi system.
Your job is to determine whether the database is the root cause of the
current alert — either through being unreachable, pool exhaustion, or
slow queries.

Work through the checks below one at a time. After each check, report
what you found before moving on.

---

## Check 1 — Is the database reachable?

Run:
```
GET https://restaurant-main.onrender.com/health
```

Report the result:
- **200 OK**: database is reachable — move to Check 2
- **503**: database (Supabase) is down — tell the engineer:
  > "The database is not reachable. Follow runbook entry 12
  > (docs/runbook.md — Downstream Dependency Failures) for next steps.
  > Check the Supabase dashboard at supabase.com for outage status."
  Stop here — do not proceed to Check 2.

---

## Check 2 — Connection pool settings

Read `backend/core/database.py` and find the `max_size` parameter in the
connection pool configuration.

Report the current value. If it is 10 or below:
> "The connection pool max_size is {value}. Under moderate traffic this
> can cause requests to queue waiting for a free connection, inflating
> p95 latency."

Ask:
> "Would you like me to increase max_size by 5 (to {value + 5})?
> I will show you the change before writing it."

If yes: show the diff, wait for confirmation, then apply the edit.
Read `docs/runbook/p95_latency_ms.md` and show the pool exhaustion fix steps.

---

## Check 3 — Slow query analysis

Run this query against the database using the DATABASE_URL from `backend/.env`:

```python
import asyncio, asyncpg

async def run():
    conn = await asyncpg.connect('<DATABASE_URL>')
    rows = await conn.fetch("""
        SELECT endpoint, 
               ROUND(AVG(duration_ms)) as avg_ms,
               MAX(duration_ms) as max_ms,
               COUNT(*) as requests
        FROM request_logs
        WHERE created_at > NOW() - INTERVAL '12 hours'
        GROUP BY endpoint
        ORDER BY avg_ms DESC
        LIMIT 10
    """)
    for r in rows:
        print(dict(r))
    await conn.close()

asyncio.run(run())
```

Show the results as a table. If any endpoint has avg_ms > 1000:
> "These endpoints are consistently slow. The queries they run likely
> need an index or optimisation."

Read `docs/runbook/p95_latency_ms.md` and show the slow query fix steps.

---

## Check 4 — Cold start test

Ask:
> "Is the high latency consistent throughout the day, or only on the
> first request after a quiet period (e.g. first request each morning)?"

If only on first request:
> "This is a Render free tier cold start. The server sleeps after 15
> minutes of inactivity and the first request pays a warm-up cost."
Read `docs/runbook/p95_latency_ms.md` and show the cold start fix steps.

---

## Reporting back

End with a clear finding statement for the orchestrator synthesis step:

> "DB layer finding: [database reachable / database unreachable /
> pool at max_size X — likely exhausted / slow queries on endpoints X, Y /
> cold start pattern detected]"
