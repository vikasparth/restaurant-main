# error_rate — Runbook Entry 13

**Threshold:** 5% (0.05) of requests returning HTTP 5xx
**Alert fires when:** threshold breached in both of the last two 6-hour windows (sustained, not a spike)

## What this means

More than 5% of all requests are failing with server errors. This is not a
brief spike — it has been sustained across two consecutive measurement windows.
Customers may be seeing errors when placing orders, making reservations, or
submitting catering enquiries.

## Most likely causes

- An unhandled exception introduced by a recent deploy
- The database (Supabase) is down or returning errors
- A route was recently changed and is now crashing on certain inputs

## Fix steps

### If errors started after a recent deploy
1. Run `git log --oneline -5` to identify the suspect commit
2. Run `git revert HEAD` to undo the last commit
3. Push and trigger a new Render deploy
4. Monitor the error rate — alert closes automatically when it drops below
   threshold in both windows

### If the database is down
Follow runbook entry 12 (Downstream Dependency Failures).
The `/health` endpoint will return 503 if the database is unreachable.

### If no recent deploy
1. Check Render logs for stack traces — identify which route is failing
2. Query `request_logs` grouped by endpoint and status code to isolate the
   failing route
3. Fix the unhandled exception and deploy

## Alert auto-closes when
Error rate drops below 5% in both consecutive 6-hour windows.
No manual action needed to close the GitHub issue.
