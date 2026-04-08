# Spec — Slice N: [Name]
**Status: DRAFT — awaiting sign-off**
**Slice tasks:** 2.N.1 → 2.N.7
**References:** architecture.md §7, §19 (shared contracts)

---

## What This Slice Does

[One paragraph — what problem does this slice solve for the customer or owner?]

---

## Endpoint

| Field | Value |
|---|---|
| Method | `GET / POST / PATCH / DELETE` |
| Path | `/api/...` |
| Auth required | Yes / No |
| Rate limited | Yes / No |

---

## Request Shape

[For GET endpoints: "No request body." For POST/PATCH: list every field with type and validation rule.]

```json
{
  "field_name": "type — validation rule"
}
```

---

## Response Shape (success)

[HTTP status code. Payload returned directly — no envelope wrapper. See architecture.md §19 Response Convention.]

```json
{}
```

---

## Business Rules

| Rule | Detail |
|---|---|
| ... | ... |

---

## Error Cases

| Scenario | HTTP Status | Error code |
|---|---|---|
| ... | ... | ... |

---

## Shared Services Used

| Service | File | Why |
|---|---|---|
| DB connection pool | `core/database.py` | All DB queries go through the shared pool |
| Config | `services/config_service.py` | If this slice reads restaurant_config |
| Timezone | `core/timezone.py` | If this slice validates times |
| Reference number | `services/reference_service.py` | If this slice generates a reference number |
| Error format | `core/errors.py` | Consistent error responses |

---

## Dependencies on Other Slices

⚠️ BEFORE FILLING THIS SECTION:
1. Read `specs/DEPENDENCY_MAP.md` — find this slice in the Quick Reference table
2. Open each listed dependency's spec file
3. Copy the exact "Signatures exposed" block from each dependency below

| Slice | File | Why needed |
|---|---|---|
| Slice N | `services/xxx_service.py` | [reason] |

```python
# Paste exact signatures copied from dependency spec files
```

**Signatures exposed by THIS slice to later slices:**

```python
# services/this_service.py

# async def function_name(params) -> ReturnType:
#     """One-line description."""
```

---

## What This Does NOT Include

- [Explicitly list what is out of scope — prevents scope creep]

---

## Test Data Setup

[What seed data must exist in the test DB before these tests can run?]

---

## Files to Create

| File | Purpose |
|---|---|
| `backend/models/xxx.py` | Pydantic models |
| `backend/services/xxx_service.py` | Business logic |
| `backend/routers/xxx.py` | HTTP layer |
| `backend/tests/test_xxx.py` | pytest tests (written before code) |
| `src/services/xxxService.ts` | Frontend fetch function |
| `src/types/xxx.ts` | TypeScript interfaces |

---

## Frontend TypeScript Contract

```typescript
export interface XxxRequest {
  // ...
}

export interface XxxResponse {
  // ...
}
```

---

## Tests to Write (Before Any Code)

| Test ID | Test name | What it verifies |
|---|---|---|
| XXX-01 | `test_...` | ... |

---

## TDD Sequence

```
Step 1 — Write tests/test_xxx.py — all tests fail
Step 2a — Write models/xxx.py
Step 2b — Run tests — still failing
Step 3a — Write services/xxx_service.py — [first function]
Step 3b — Write services/xxx_service.py — [second function]
Step 3c — Write routers/xxx.py
Step 3d — Run tests — most should go green
Step 4  — Fix any remaining failures
Step 5  — All tests green — backend done
Step 6  — Write src/types/xxx.ts
Step 7  — Write src/services/xxxService.ts
Step 8  — Wire to UI page
Step 9  — Manual verification in browser
```

---

## Sign-off

- [ ] Vikas reviewed and approved this spec
- [ ] All tests written and failing before any code written
- [ ] All tests passing before moving to next slice
- [ ] Full test suite run (not just this slice's tests) — all passing
