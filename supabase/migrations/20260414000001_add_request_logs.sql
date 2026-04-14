-- Request logs: records every HTTP request for monitoring metrics
-- Fields: method, path, status_code, duration_ms, request_id (correlation ID)
CREATE TABLE request_logs (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    method      TEXT NOT NULL,
    path        TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    request_id  TEXT NOT NULL
);

-- Time-based index: monitoring agent queries this table by time window
CREATE INDEX idx_request_logs_created_at ON request_logs (created_at DESC);

-- 30-day retention: runs nightly at 3am to prevent unbounded table growth
SELECT cron.schedule(
    'delete-old-request-logs',
    '0 3 * * *',
    $$DELETE FROM request_logs WHERE created_at < now() - INTERVAL '30 days'$$
);
