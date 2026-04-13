from core.config import settings


async def validate_zip(db, zip_code: str) -> dict | None:
    """Returns {"zip_code": str, "city": str} if covered, or None if not."""
    row = await db.fetchrow(
        """
        SELECT zip_code, city
        FROM delivery_zones
        WHERE zip_code = $1
          AND location_id = $2
          AND is_active = true
        """,
        zip_code.strip(),
        settings.location_id,
    )
    return dict(row) if row else None
