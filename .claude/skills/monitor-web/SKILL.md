# monitor-web — Render Service and Deploy Checks

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

Run `git log --oneline -5` and show the output.

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
> Then read `docs/runbook/error_rate.md` and show the fix steps for
> the deploy scenario.

If no: move to Check 3.

---

## Check 3 — Render logs (manual review)

Render logs cannot be fetched automatically yet — this will be available
once the MCP server is built in task 3.13 (`get_render_logs()` tool).

Ask the engineer:
> "Would you like to review Render logs manually? If yes, go to:
> Render dashboard → Services → `restaurant-main` → Logs
>
> Look for any of the following in the last 30 minutes:
> - `Exception`, `Error`, `Traceback`
> - A route name followed by a status code (e.g. `POST /api/orders 500`)
> - Any repeated error pattern
>
> Paste anything suspicious here and I will help you interpret it.
> Or type 'skip' if you want to close the check."

If they paste a stack trace: identify the file, line number, and error type.
Read the relevant runbook entry and suggest the fix.

If nothing found or they skip: web layer is clear.

---

## Reporting back

End with a clear finding statement for the orchestrator synthesis step:

> "Web layer finding: [Render is healthy / deploy at HH:MM is suspect /
> service was sleeping / stack trace found in route X]"
