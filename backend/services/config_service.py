import json
from core.config import settings


async def get_restaurant_config(db) -> dict:
    """Fetch the restaurant config row for the configured location."""
    row = await db.fetchrow(
        """
        SELECT timezone,
               operating_hours,
               closed_days,
               delivery_fee,
               min_delivery_order,
               min_catering_order,
               catering_advance_hours,
               catering_deposit_percent,
               max_reservation_party_size
        FROM   restaurant_config
        WHERE  location_id = $1
        """,
        settings.location_id,
    )
    if row is None:
        raise RuntimeError("Restaurant config not found for this location")
    result = dict(row)
    # asyncpg returns JSONB as a string — parse it into a dict
    if isinstance(result["operating_hours"], str):
        result["operating_hours"] = json.loads(result["operating_hours"])
    return result
