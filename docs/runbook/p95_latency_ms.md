# p95_latency_ms — Runbook Entry 14

**Threshold:** 2000ms
**Alert fires when:** threshold breached in both of the last two 6-hour windows (sustained, not a spike)

## What this means

"p95 latency" means: 95% of requests completed faster than this value. The
slowest 5% of requests are taking more than 2 seconds. This is sustained —
not a single slow request. Customers may notice the site feeling sluggish.

## Most likely causes

- A database query is slow because a table has grown large or an index is missing
- The database connection pool is near capacity — requests queue waiting for a
  connection to free up
- Render free tier cold starts — the first request after the server sleeps is
  slow (this only inflates p95 if traffic is very low)

## Fix steps

### If slow database queries
1. Find the slowest endpoints:
   ```sql
   SELECT endpoint, AVG(duration_ms), MAX(duration_ms), COUNT(*)
   FROM request_logs
   ORDER BY AVG(duration_ms) DESC
   LIMIT 10;
   ```
2. Run `EXPLAIN ANALYZE` on the queries those endpoints use
3. Add a missing index or rewrite the slow query
4. Deploy the fix — alert closes automatically once latency recovers

### If connection pool exhaustion
1. Check `backend/core/database.py` — find the `max_size` parameter
2. Increase it by 5 (e.g. 10 → 15)
3. Deploy — watch p95 in the next monitor run

### If cold starts
1. Confirm by checking if latency only affects the first request after a
   quiet period (p95 is high but median is normal)
2. Long-term fix: upgrade Render to a paid tier to keep the instance warm
3. Short-term: set up a keep-alive ping (pings the /health endpoint every
   10 minutes to prevent sleep)

## Alert auto-closes when
p95 latency drops below 2000ms in both consecutive 6-hour windows.
No manual action needed to close the GitHub issue.
