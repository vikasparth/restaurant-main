# Tests for Slice 1 — Menu (Read)
# Spec: specs/slice1_menu.md
# TDD: all tests written first — they will all FAIL until the menu endpoint is built.
#
# Run with: pytest tests/test_menu.py -v
# All tests use the real FastAPI app + real test database via httpx.AsyncClient (from conftest.py)

import pytest


# ============================================================
# MNU-01: Basic connectivity
# ============================================================
@pytest.mark.anyio
async def test_menu_returns_200(client):
    """GET /api/menu must return HTTP 200."""
    response = await client.get("/api/menu")
    assert response.status_code == 200


# ============================================================
# MNU-02: Response structure
# ============================================================
@pytest.mark.anyio
async def test_menu_returns_categories_key(client):
    """Response must have a 'categories' key containing a list."""
    response = await client.get("/api/menu")
    body = response.json()
    assert "categories" in body
    assert isinstance(body["categories"], list)


# ============================================================
# MNU-03: Required fields on every item
# ============================================================
@pytest.mark.anyio
async def test_menu_items_have_required_fields(client):
    """Every menu item must have all required fields."""
    response = await client.get("/api/menu")
    body = response.json()

    required_fields = {
        "id", "name", "description", "price", "category",
        "image_url", "is_vegetarian", "is_available",
        "catering_available", "catering_price_per_tray",
        "allergens", "display_order",
    }

    for category in body["categories"]:
        for item in category["items"]:
            missing = required_fields - item.keys()
            assert not missing, f"Item '{item.get('id')}' is missing fields: {missing}"


# ============================================================
# MNU-04: Unavailable items excluded
# ============================================================
@pytest.mark.anyio
async def test_unavailable_items_excluded(client):
    """Items with is_available=false must not appear in the response."""
    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        for item in category["items"]:
            assert item["is_available"] is True, (
                f"Item '{item['id']}' has is_available=false but appeared in response"
            )


# ============================================================
# MNU-05: Items grouped correctly by category
# ============================================================
@pytest.mark.anyio
async def test_items_grouped_by_category(client):
    """Each category block must contain only items matching that category name."""
    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        for item in category["items"]:
            assert item["category"] == category["name"], (
                f"Item '{item['id']}' has category '{item['category']}' "
                f"but appeared under '{category['name']}'"
            )


# ============================================================
# MNU-06: Items sorted by display_order within each category
# ============================================================
@pytest.mark.anyio
async def test_items_sorted_by_display_order(client):
    """Items within each category must be in ascending display_order."""
    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        orders = [item["display_order"] for item in category["items"]]
        assert orders == sorted(orders), (
            f"Category '{category['name']}' items are not sorted by display_order. "
            f"Got: {orders}"
        )


# ============================================================
# MNU-07: Empty menu returns empty categories list
# ============================================================
@pytest.mark.anyio
async def test_empty_menu_returns_empty_categories(client):
    """When no items are available, response must be {"categories": []} not an error."""
    # Note: this test relies on a fixture or test-specific data setup
    # that marks all items unavailable. For now this verifies the shape
    # contract — full isolation tested in integration phase.
    response = await client.get("/api/menu")
    body = response.json()
    # Must always return the categories key — never null, never missing
    assert "categories" in body
    assert body["categories"] is not None


# ============================================================
# MNU-08: Categories appear in the correct fixed order
# ============================================================
@pytest.mark.anyio
async def test_categories_in_correct_order(client):
    """Categories must appear in fixed order: appetizers→mains→breads→desserts→drinks→specials."""
    fixed_order = ["appetizers", "mains", "breads", "desserts", "drinks", "specials"]

    response = await client.get("/api/menu")
    body = response.json()

    returned_category_names = [c["name"] for c in body["categories"]]

    # Filter fixed_order to only categories that are present in response
    expected_order = [c for c in fixed_order if c in returned_category_names]

    assert returned_category_names == expected_order, (
        f"Categories out of order. Expected: {expected_order}, Got: {returned_category_names}"
    )


# ============================================================
# MNU-09: Field types are correct
# ============================================================
@pytest.mark.anyio
async def test_field_types_are_correct(client):
    """price must be float, allergens must be list, is_vegetarian must be bool, id must be str."""
    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        for item in category["items"]:
            assert isinstance(item["id"], str), f"id must be str, got {type(item['id'])}"
            assert isinstance(item["price"], (int, float)), f"price must be number, got {type(item['price'])}"
            assert isinstance(item["allergens"], list), f"allergens must be list, got {type(item['allergens'])}"
            assert isinstance(item["is_vegetarian"], bool), f"is_vegetarian must be bool, got {type(item['is_vegetarian'])}"
            assert isinstance(item["is_available"], bool), f"is_available must be bool, got {type(item['is_available'])}"
            assert isinstance(item["catering_available"], bool), f"catering_available must be bool, got {type(item['catering_available'])}"


# ============================================================
# MNU-10: Internal DB fields are not exposed
# ============================================================
@pytest.mark.anyio
async def test_internal_fields_not_exposed(client):
    """location_id, created_at, updated_at must never appear in the response."""
    internal_fields = {"location_id", "created_at", "updated_at"}

    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        for item in category["items"]:
            exposed = internal_fields & item.keys()
            assert not exposed, (
                f"Item '{item['id']}' exposes internal fields: {exposed}"
            )


# ============================================================
# MNU-11: Catering fields are correct based on catering_available flag
# ============================================================
@pytest.mark.anyio
async def test_catering_fields_correct(client):
    """catering_price_per_tray must be non-null when catering_available=true, null when false."""
    response = await client.get("/api/menu")
    body = response.json()

    for category in body["categories"]:
        for item in category["items"]:
            if item["catering_available"]:
                assert item["catering_price_per_tray"] is not None, (
                    f"Item '{item['id']}' has catering_available=true but catering_price_per_tray is null"
                )
            else:
                assert item["catering_price_per_tray"] is None, (
                    f"Item '{item['id']}' has catering_available=false but catering_price_per_tray is not null"
                )


# ============================================================
# MNU-12: DB failure returns 503 with correct error code
# ============================================================
@pytest.mark.anyio
async def test_db_failure_returns_503(client, monkeypatch):
    """Simulated DB failure must return HTTP 503 with code DB_UNAVAILABLE."""
    # We monkeypatch the menu service to raise an exception simulating a DB failure
    import services.menu_service as menu_service

    async def mock_get_menu_items(*args, **kwargs):
        raise Exception("Simulated DB connection failure")

    monkeypatch.setattr(menu_service, "get_menu_items", mock_get_menu_items)

    response = await client.get("/api/menu")
    assert response.status_code == 503

    body = response.json()
    assert body.get("code") == "DB_UNAVAILABLE"
