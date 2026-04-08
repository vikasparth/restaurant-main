# Spec — Slice 1: Menu (Read)
**Status: APPROVED — Signed off by Vikas, 2026-04-07**
**Slice tasks:** 2.1.1 → 2.1.7
**References:** architecture.md §7, §6 (menu_items table), §12 (testing strategy)

---

## What This Slice Does

Enables the React frontend to load menu items from the Supabase database instead of the static `menu.ts` file.

---

## Endpoint

| Field | Value |
|---|---|
| Method | `GET` |
| Path | `/api/menu` |
| Auth required | No — public |
| Rate limited | No — read-only, no abuse risk |

---

## Request Shape

No request body. No query parameters. No headers required.

---

## Response Shape (success)

HTTP 200. Payload returned directly — no envelope wrapper (see architecture.md §Response Convention).

```json
{
  "categories": [
    {
      "name": "appetizers",
      "items": [
        {
          "id": "samosa",
          "name": "Samosa",
          "description": "Crispy pastry filled with spiced potatoes and peas",
          "price": 5.99,
          "category": "appetizers",
          "image_url": "/images/samosa.jpg",
          "is_vegetarian": true,
          "is_available": true,
          "catering_available": true,
          "catering_price_per_tray": 35.00,
          "allergens": ["gluten"],
          "display_order": 1
        }
      ]
    }
  ]
}
```

**Field notes:**
- `id` — text slug (e.g. `"samosa"`, `"butter-chicken"`), NOT a UUID
- `price` — number (float), never a string
- `allergens` — always a list, empty list `[]` if none
- `catering_price_per_tray` — null if `catering_available` is false
- Internal fields (`location_id`, `created_at`, `updated_at`) are never returned

---

## Business Rules

| Rule | Detail |
|---|---|
| Unavailable items excluded | Only items where `is_available = true` are returned |
| Grouped by category | Items grouped by their `category` field |
| Category order fixed | Categories always appear in this order: `appetizers → mains → breads → desserts → drinks → specials` |
| Items sorted within category | Items sorted by `display_order` ascending |
| Category disappears if empty | If all items in a category are unavailable, that category does not appear in the response |
| Empty menu | If zero items are available, return `{"categories": []}` — not an error |
| Location | Queries items for `DEFAULT_LOCATION_ID` from environment config (see architecture.md §location_id Strategy) |

---

## Error Cases

| Scenario | HTTP Status | Error code |
|---|---|---|
| Database connection failure | 503 | `DB_UNAVAILABLE` |

Error response format: `{"error": "Service temporarily unavailable", "code": "DB_UNAVAILABLE"}`

No other error cases — there are no inputs to validate on a GET endpoint.

---

## Shared Services Used

| Service | File | Why |
|---|---|---|
| DB connection pool | `core/database.py` | All DB queries go through the shared pool |
| Config (location_id) | `core/config.py` | Reads `DEFAULT_LOCATION_ID` from env |
| Error format | `core/errors.py` | Consistent error responses |

No other shared services needed for this slice.

---

## Dependencies on Other Slices

| Dependency | Detail |
|---|---|
| None | Slice 1 is the foundation — no other slice is required before this one |

**Signatures exposed to later slices:**

These are the exact function signatures that other slices must consume. When writing a dependent slice, inject these signatures as context — do not re-read the full file.

```python
# services/menu_service.py

async def get_menu_items(db) -> list[dict]:
    """Returns all available menu items for the default location as a flat list of dicts."""

async def validate_menu_items(db, item_ids: list[str]) -> None:
    """Raises HTTP 422 INVALID_MENU_ITEM if any id is not found or is_available=false."""
```

```python
# models/menu.py — MenuItem shape (move to models/shared.py before Slice 3)

class MenuItem(BaseModel):
    id: str                              # text slug e.g. "samosa"
    name: str
    description: str
    price: float
    category: str
    image_url: str
    is_vegetarian: bool
    is_available: bool
    catering_available: bool
    catering_price_per_tray: float | None
    allergens: list[str]
    display_order: int
```

**Consumed by:**
- Slice 3 (Orders): calls `validate_menu_items()` before saving; uses `MenuItem.id` and `MenuItem.price`
- Slice 5 (Catering): calls `validate_menu_items()` before saving; uses `MenuItem.catering_available` and `MenuItem.catering_price_per_tray`
- Slice 7 (Admin Menu CRUD): extends `menu_service.py` with write operations — must not change existing function signatures

---

## What This Does NOT Include

- Adding, editing, or deleting menu items (Slice 7 — Admin Menu CRUD)
- Daily specials (Phase 2)
- Menu item images from Supabase Storage (Phase 2 — currently static files in frontend)
- Pagination (not needed for a single restaurant menu)

---

## Test Data Setup

Tests rely on the standard seed data from `20260406000002_seed_data.sql` being present in the test database. Specifically:

- At least 2 categories with multiple items (appetizers, mains)
- At least 1 item with `is_available = false` (needed for MNU-04)
- At least 1 item with `catering_available = false` and `catering_price_per_tray = null` (mango-lassi)
- At least 1 item with `catering_available = true` and a non-null `catering_price_per_tray`

`conftest.py` handles DB setup/teardown between tests to prevent test interference.

---

## Files to Create

| File | Purpose |
|---|---|
| `backend/models/menu.py` | Pydantic models: `MenuItem`, `MenuCategory`, `MenuResponse` |
| `backend/services/menu_service.py` | Business logic: fetch + filter + group items from DB |
| `backend/routers/menu.py` | HTTP layer: `GET /api/menu` route |
| `backend/tests/test_menu.py` | pytest tests (written before the code) |
| `src/services/menuService.ts` | Frontend: fetch from API instead of static file |

---

## Frontend TypeScript Contract

The frontend `menuService.ts` must use these types (to be created in `src/types/menu.ts`):

```typescript
export interface MenuItem {
  id: string;                          // text slug e.g. "samosa"
  name: string;
  description: string;
  price: number;
  category: string;
  image_url: string;
  is_vegetarian: boolean;
  is_available: boolean;
  catering_available: boolean;
  catering_price_per_tray: number | null;
  allergens: string[];
  display_order: number;
}

export interface MenuCategory {
  name: string;
  items: MenuItem[];
}

export interface MenuResponse {
  categories: MenuCategory[];
}
```

---

## Tests to Write (Before Any Code)

All tests use `httpx.AsyncClient` against the real FastAPI test app and real test database. Tests are written first — all fail — then code is written to make them pass.

| Test ID | Test name | What it verifies |
|---|---|---|
| MNU-01 | `test_menu_returns_200` | `GET /api/menu` returns HTTP 200 |
| MNU-02 | `test_menu_returns_categories_key` | Response has a `categories` key containing a list |
| MNU-03 | `test_menu_items_have_required_fields` | Every item has `id`, `name`, `description`, `price`, `category`, `image_url`, `is_vegetarian`, `allergens`, `display_order` |
| MNU-04 | `test_unavailable_items_excluded` | Items with `is_available = false` are not in the response |
| MNU-05 | `test_items_grouped_by_category` | Each category block contains only items matching that category name |
| MNU-06 | `test_items_sorted_by_display_order` | Items within a category appear in ascending `display_order` |
| MNU-07 | `test_empty_menu_returns_empty_categories` | When all items are unavailable, response is `{"categories": []}` |
| MNU-08 | `test_categories_in_correct_order` | Categories appear in fixed order: appetizers → mains → breads → desserts → drinks → specials |
| MNU-09 | `test_field_types_are_correct` | `price` is float, `allergens` is list, `is_vegetarian` is bool, `id` is string |
| MNU-10 | `test_internal_fields_not_exposed` | `location_id`, `created_at`, `updated_at` are absent from every item |
| MNU-11 | `test_catering_fields_correct` | Item with `catering_available=true` has non-null `catering_price_per_tray`; item with `catering_available=false` has null `catering_price_per_tray` |
| MNU-12 | `test_db_failure_returns_503` | Simulated DB failure returns HTTP 503 with `{"error": "...", "code": "DB_UNAVAILABLE"}` |

---

## TDD Sequence (How We Will Build This)

```
Step 1 — Write tests/test_menu.py — all 12 tests fail (no code exists)
Step 2a — Write models/menu.py — define MenuItem, MenuCategory, MenuResponse
Step 2b — Run tests — still failing (no DB query yet)
Step 3a — Write services/menu_service.py — get_menu_items() DB query function
Step 3b — Write group_by_category() function to organise items
Step 3c — Write routers/menu.py — wire service to GET /api/menu
Step 3d — Run tests — MNU-01 through MNU-11 should go green
Step 4  — Fix MNU-12 (DB failure simulation) — may need a fixture tweak
Step 5  — All 12 tests green — backend done
Step 6  — Write src/types/menu.ts TypeScript types
Step 7  — Write src/services/menuService.ts fetch function
Step 8  — Update MenuPage.tsx to use API instead of static menu.ts
Step 9  — Manual verification in browser
```

---

## Sign-off

- [x] Vikas reviewed and approved this spec ✅ 2026-04-07
- [ ] All 12 tests written and failing before any code written
- [ ] All 12 tests passing before moving to Slice 2
