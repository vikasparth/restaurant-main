from pydantic import BaseModel


class MenuItem(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    is_vegetarian: bool
    is_available: bool
    catering_available: bool
    catering_price_per_tray: float | None  # None means null — allowed when catering_available=false
    allergens: list[str]                   # e.g. ["gluten", "dairy"] — empty list if none
    display_order: int


class MenuCategory(BaseModel):
    name: str
    items: list[MenuItem]


class MenuResponse(BaseModel):
    categories: list[MenuCategory]
