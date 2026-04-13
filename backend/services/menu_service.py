from core.config import settings
from models.menu import MenuCategory, MenuItem, MenuResponse

CATEGORY_ORDER = ["appetizers", "mains", "breads", "desserts", "drinks", "specials"]


async def get_menu_items(db) -> list[dict]:
    rows = await db.fetch(
        """
        SELECT id, name, description, price, category, image_url,
               is_vegetarian, is_available, catering_available,
               catering_price_per_tray, allergens, display_order
        FROM menu_items
        WHERE is_available = true
          AND location_id = $1
        ORDER BY display_order ASC
        """,
        settings.location_id,
    )
    return [dict(row) for row in rows]


async def validate_menu_items(db, item_ids: list[str]) -> None:
    """Raises HTTP 422 INVALID_MENU_ITEM if any id is not found or is_available=false."""
    from fastapi import HTTPException

    rows = await db.fetch(
        """
        SELECT id FROM menu_items
        WHERE  id = ANY($1::text[])
          AND  location_id = $2
          AND  is_available = true
        """,
        item_ids,
        settings.location_id,
    )
    found_ids = {row["id"] for row in rows}
    for item_id in item_ids:
        if item_id not in found_ids:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"Menu item not found or unavailable: {item_id}",
                    "code": "INVALID_MENU_ITEM",
                },
            )


def group_by_category(rows: list[dict]) -> MenuResponse:
    grouped = {}
    for row in rows:
        cat = row["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(MenuItem(**row))

    categories = []
    for cat_name in CATEGORY_ORDER:
        if cat_name in grouped:
            categories.append(MenuCategory(name=cat_name, items=grouped[cat_name]))

    return MenuResponse(categories=categories)
