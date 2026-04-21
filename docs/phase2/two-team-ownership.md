# Two-Team Ownership Setup
**Status:** ⏳ Pending — task 3.15 in execution-plan.md

## Goal

Work backwards from this reality — a frontend team owns `lovable_project`, a backend team owns `restaurant_main_project`. They integrate via a published API contract. Neither team should need to read the other team's source code to do their job.

## What breaks today without this

- Frontend assumes field names by reading Python source or by memory — breaks silently when backend refactors
- No shared contract means integration failures are discovered in production, not in CI
- A new frontend engineer has no rules, no Claude guidance, and no defined boundary

## Changes required

- [ ] Export `openapi.json` from FastAPI and commit it to the backend repo — add `scripts/export_openapi.py` so any engineer can regenerate it; this file is the single source of truth for the API contract
- [ ] Add rule to `backend/CLAUDE.md`: any change to a public endpoint shape, field name, or status code requires regenerating and committing `openapi.json` before merging — contract changes are visible in git diff, not buried in implementation
- [ ] Create `lovable_project/CLAUDE.md` — frontend-only Claude rules: read the API contract from `../restaurant_main_project/openapi.json`, never hand-write TypeScript types that duplicate the spec, never call endpoints not listed in the spec, mock the backend using the spec during development
- [ ] Split root `CLAUDE.md` so org-wide rules (git conventions, ADR process, engineering principles) are clearly separated from backend-specific rules — each team's Claude reads only what applies to them
