-- ============================================================
-- Migration: Add pg_cron job for reservation reminders
-- Reason: RES-09 — daily 9am Pacific reminder emails via Supabase pg_cron + pg_net
--
-- Prerequisites (enable once in Supabase dashboard):
--   Database → Extensions → pg_cron  (enable)
--   Database → Extensions → pg_net   (enable)
--
-- Supabase config vars to set in dashboard (Database → Config):
--   app.api_base_url  = https://your-render-app.onrender.com
--   app.internal_token = <same value as INTERNAL_TOKEN env var>
--
-- Schedule: 0 17 * * * = 9am PDT (UTC-7). Change to 0 16 * * * in PST (UTC-8, Nov–Mar).
-- ============================================================

select cron.schedule(
  'send-reservation-reminders',
  '0 17 * * *',
  $$
    select net.http_post(
      url     := current_setting('app.api_base_url') || '/api/internal/send-reminders',
      headers := jsonb_build_object(
        'Content-Type',     'application/json',
        'X-Internal-Token', current_setting('app.internal_token')
      ),
      body    := '{}'::jsonb
    )
  $$
);
