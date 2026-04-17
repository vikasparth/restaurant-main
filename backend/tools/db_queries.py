import asyncpg
from core.config import settings

async def query_request_logs(window_hours: int = 12):
    try:
        conn = await asyncpg.connect(settings.database_url)
        rows = await conn.fetch(f"""
            SELECT path, status_code,
                   ROUND(AVG(duration_ms)) AS avg_ms,
                   MAX(duration_ms) AS max_ms,
                   COUNT(*) AS requests
            FROM request_logs
            WHERE created_at > NOW() - INTERVAL '{window_hours} hours'
            GROUP BY path, status_code
            ORDER BY avg_ms DESC
            LIMIT 10
        """)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def query_notification_failures(window_hours: int = 12):
    try:
        conn = await asyncpg.connect(settings.database_url)
        rows = await conn.fetch(f"""
            SELECT provider, error_code, COUNT(*) AS failures
            FROM notification_logs
            WHERE success = false
                AND created_at > NOW() - INTERVAL '{window_hours} hours'
            GROUP BY provider, error_code
            ORDER BY failures DESC
                         """)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": str(e)}
