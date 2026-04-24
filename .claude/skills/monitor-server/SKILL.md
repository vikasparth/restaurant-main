# monitor-server — Render Service and Deploy Checks

You are investigating the **web layer** of the Aap ki Rasoi system.
Your job is to determine whether the Render service or a recent deploy
is the root cause of the current alert — or, when all metrics are healthy,
to offer a manual Render log review as a final confidence check.

Work through the checks below one at a time. After each check, report
what you found and ask the engineer what they see before moving on.

**If called from the all-healthy path:** skip Check 1 (server is already
confirmed up from Step 1). Run Check 2 and Check 3 only.

---

## Check 1 — Is the Render service awake?

Ask the engineer:
> "Go to Render dashboard → Services → `restaurant-main`. What is the status?
>
> - Green (Running): service is awake — move to Check 2
> - Yellow (Deploying): wait 2-3 minutes then try the monitor endpoint again
> - Red (Failed): the service crashed — go to Render logs and look for the
>   last error before the crash
> - Grey (Suspended): free tier sleep — click 'Manual Deploy' to wake it,
>   then wait 2-3 minutes and try again
>
> What do you see?"

Wait for the engineer to reply before continuing.

---

## Check 2 — Recent bad deploy?

Call MCP tool `get_recent_commits()` and show the last 5 commits (sha, message, author, committed_at).

Ask:
> "Here are the last 5 commits. Does the timing of any of these match
> when the alert started or the server became slow/unresponsive?"

If yes:
> "Would you like me to revert that commit now? I will show you exactly
> what will change before doing anything."
>
> If yes: show the commit details (`git show HEAD --stat`), confirm with
> the engineer, then run `git revert HEAD`.
> Remind them to push and trigger a new Render deploy afterward.
>
> Then read `backend/docs/runbook/error_rate.md` and show the fix steps for
> the deploy scenario.

If no: move to Check 3.

---

## Check 3 — Render logs (automatic)

**Do not skip this step, even if Check 2 found no bad deploy.** Render logs
may contain stack traces or 500 errors that are not visible in the metrics
table.

**Before calling `get_render_logs()`:** check if Render logs are already in
context from this session (look for "Render logs (fetched at ...)"). If yes,
use those. If no, call `get_render_logs(lines=100)` now and note the result
as "Render logs (fetched at monitor-server Check 3)".

Look for any of the following:
- `Exception`, `Error`, `Traceback`
- A route name followed by a 5xx status code (e.g. `POST /api/orders 500`)
- Any repeated error pattern

If suspicious lines are found: identify the file, line number, and error type.
Read the relevant runbook entry and suggest the fix.

If nothing found: web layer is clear.

---

## Reporting back

End with a clear finding statement for the orchestrator synthesis step:

> "Web layer finding: [Render is healthy / deploy at HH:MM is suspect /
> service was sleeping / stack trace found in route X]"
