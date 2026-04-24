# notification_failures — Runbook Entry 15

**Threshold:** 2 failures per window
**Alert fires when:** threshold breached in both of the last two 6-hour windows (sustained, not a spike)

## What this means

More than 2 email or WhatsApp notification sends failed in each of the last
two 6-hour windows. Customers may not be receiving order confirmations,
reservation updates, or catering enquiry acknowledgements.

## Most likely causes

- Resend (email) or Twilio (WhatsApp) free tier quota exhausted
- API credentials expired or were rotated but not updated in Render
- A provider outage

## Fix steps

### Step 1 — Identify which provider is failing
Query the notification logs:
```sql
SELECT provider, error_code, COUNT(*) as failures
FROM notification_logs
WHERE success = false
  AND created_at > NOW() - INTERVAL '12 hours'
GROUP BY provider, error_code
ORDER BY failures DESC;
```

### If Resend (email) is failing

**Quota exhausted:**
- Check resend.com dashboard → Usage
- Short-term: set `NOTIFICATIONS_ENABLED=false` in Render env vars
- Long-term: upgrade Resend plan or reduce email send frequency

**Invalid API key:**
- Go to Render → Environment → verify `RESEND_API_KEY` is set and non-blank
- Regenerate the key at resend.com if needed, update Render env var, redeploy

**Provider outage:**
- Check https://status.resend.com/
- Set `NOTIFICATIONS_ENABLED=false` temporarily until resolved

### If Twilio (WhatsApp) is failing

**Quota exhausted:**
- Check console.twilio.com → Monitor → Usage
- Short-term: set `NOTIFICATIONS_ENABLED=false` in Render env vars

**Invalid credentials:**
- Go to Render → Environment → verify `TWILIO_ACCOUNT_SID` and
  `TWILIO_AUTH_TOKEN` are set correctly
- Check console.twilio.com to confirm the credentials are active

**WhatsApp sandbox expired:**
- The Twilio WhatsApp sandbox requires periodic re-joining
- Ask the owner to send "join <sandbox-keyword>" to the Twilio WhatsApp number

**Provider outage:**
- Check https://status.twilio.com/
- Set `NOTIFICATIONS_ENABLED=false` temporarily until resolved

### Disabling notifications temporarily
Update in Render env vars (not just `.env` — local file does not affect production):
```
NOTIFICATIONS_ENABLED=false
```
Trigger a manual deploy. Re-enable once the provider issue is resolved.

## Alert auto-closes when
Notification failure count drops below 2 in both consecutive 6-hour windows.
No manual action needed to close the GitHub issue.
