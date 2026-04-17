# monitor-dependencies — Resend and Twilio Status Checks

You are investigating the **dependencies layer** of the Aap ki Rasoi system.
Your job is to determine whether Resend (email) or Twilio (WhatsApp) is the
root cause of notification failures.

Work through the checks below one at a time. After each check, report
what you found before moving on.

---

## Check 1 — Provider status pages

Call MCP tools in parallel:
- `check_provider_status(provider="resend")`
- `check_provider_status(provider="twilio")`

Interpret the `raw_status` field from each response and report one line each:
- `Resend — Operational` or `Resend — Degraded / Outage`
- `Twilio — Operational` or `Twilio — Degraded / Outage`

If either is degraded or down:
> "This provider is experiencing issues. This is likely the root cause
> of notification failures. Read docs/runbook/notification_failures.md
> for the provider outage fix steps."

If both are operational: move to Check 2 — the failure is coming from inside the application, not the provider.

---

## Check 2 — Query recent failure logs

Call MCP tool `query_notification_failures(window_hours=12)` and show the results.

Based on the `error_code`:

- `API key is invalid` → credentials issue — move to Check 3
- `quota exceeded` / `rate limit` → quota issue — read
  `docs/runbook/notification_failures.md` quota fix steps
- Blank or unrecognised error code → move to Check 2a
- Any other known error → read `docs/runbook/notification_failures.md`
  and match to the appropriate fix scenario

### Check 2a — Render logs fallback

If error code is blank or unrecognised, do not ask the engineer to check
the dashboard manually. Call the MCP tool directly:

**Before calling `get_render_logs()`:** check if Render logs are already in
context from this session (look for "Render logs (fetched at ...)"). If yes,
use those. If no, call `get_render_logs(lines=100)` now and note the result
as "Render logs (fetched at monitor-dependencies Check 2a)".

Scan for notification-related exceptions:
- Lines containing `resend`, `twilio`, `send_email`, `send_whatsapp`
- `Exception`, `Error`, `Traceback` near notification code paths

If a pattern is found: identify the error and suggest the fix.

If nothing found:
> "Both providers are operational, failure logs show no known error code,
> and Render logs are clean. The failures may be intermittent or already
> resolved. Monitor for recurrence over the next window."

---

## Check 3 — Render env var verification

If error_code indicates a credentials problem, ask:
> "Go to Render → Environment tab. Verify these are set and non-blank:
> - `RESEND_API_KEY` (for email)
> - `TWILIO_ACCOUNT_SID` (for WhatsApp)
> - `TWILIO_AUTH_TOKEN` (for WhatsApp)
>
> Are they all present and non-blank?"

If any are missing or blank:
> "That is the root cause. Re-enter the correct value in Render and
> trigger a manual deploy."

Read `docs/runbook/notification_failures.md` and show the credentials fix steps.

---

## Check 4 — Offer to disable notifications temporarily

If the issue cannot be resolved immediately:
> "Would you like me to set `NOTIFICATIONS_ENABLED=false` in `backend/.env`
> to stop further failure logging while you investigate?"
>
> If yes: read `backend/.env`, set `NOTIFICATIONS_ENABLED=false`.
> Important: also remind the engineer to update this in Render env vars —
> the local `.env` file does not affect the live production server.

---

## Reporting back

End with a clear finding statement for the orchestrator synthesis step:

> "Dependencies layer finding: [Resend operational / Twilio degraded /
> invalid API key for {provider} / quota exhausted for {provider} /
> credentials missing in Render env vars]"
