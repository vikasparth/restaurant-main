# Slice Dependency Map
**Read this before writing any new spec.**
For each slice, this tells you: which earlier slices to pull signatures from.

---

## Quick Reference

| Slice being written | Must pull signatures from |
|---|---|
| Slice 1 — Menu (Read) | None |
| Slice 2 — Delivery Validation | None |
| Slice 3 — Orders | Slice 1 (`validate_menu_items`), Slice 2 (`validate_zip`) |
| Slice 4 — Reservations | None |
| Slice 5 — Catering | Slice 1 (`validate_menu_items`, `MenuItem.catering_available`) |
| Slice 6 — Notifications | Slice 3, 4, 5 (wires into their services — read all three) |
| Slice 7 — Menu Admin CRUD | Slice 1 (extends `menu_service.py` — must not break existing signatures) |
| Slice 8 — Admin Endpoints | Slice 3, 4, 5, 7 (reads from all their services) |

---

## Shared Services (always inject when the slice uses them)

| Service | File | Used by slices |
|---|---|---|
| DB connection | `core/database.get_db()` | All |
| Location ID | `core/config.settings.location_id` | All |
| Restaurant config | `services/config_service.get_restaurant_config(db)` | 3, 4, 5, 8 |
| Reference number | `services/reference_service.generate_reference_number(db)` | 3, 4, 5 |
| Timezone | `core/timezone.to_restaurant_time(dt, tz)` | 3, 4, 5 |
| Menu validation | `services/menu_service.validate_menu_items(db, ids)` | 3, 5 |
| Error format | `core/errors.py` | All |

---

## Where to Find Signatures

Each spec has a **"Signatures exposed to later slices"** block in its Dependencies section.
When the table above says "pull from Slice 1", go to `specs/slice1_menu.md` → Dependencies → copy those signatures into the new spec.

**Process when starting a new spec:**
1. Check the Quick Reference table above for this slice
2. Open each listed dependency's spec file
3. Copy the "Signatures exposed" block into the new spec's Dependencies section
4. Only then start writing the spec body
