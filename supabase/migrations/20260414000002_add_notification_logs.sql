-- Notification logs: records every email/WhatsApp send attempt
-- No PII — identified by reference number only
CREATE TABLE notification_logs (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    provider    TEXT NOT NULL,
    channel     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    reference   TEXT NOT NULL,
    success     BOOLEAN NOT NULL,
    error_code  TEXT
);

CREATE INDEX idx_notification_logs_created_at ON notification_logs (created_at DESC);
CREATE INDEX idx_notification_logs_reference ON notification_logs (reference);

-- 30-day retention: runs nightly at 3am to prevent unbounded table growth
SELECT cron.schedule(
    'delete-old-notification-logs',
    '0 3 * * *',
    $$DELETE FROM notification_logs WHERE created_at < now() - INTERVAL '30 days'$$
);
