# Project Rules — Restaurant Management System

## Workspace Scope
- You MUST operate ONLY inside the `main_project` directory.
- Never modify files inside ../lovable_project.
- Treat ../lovable_project as READ-ONLY reference.

## Migration Rules
When asked to migrate UI:

1. ONLY analyze files changed in the latest commit of ../lovable_project.
2. DO NOT scan entire repository history.
3. DO NOT re-copy unchanged files.
4. Copy only newly added or modified components.

### STRICT: Visual Preservation — Zero Tolerance
**You MUST NOT change any of the following during migration:**
- CSS classes, Tailwind classes, or className values
- Layout structure (grid, flex, positioning, spacing)
- Color scheme, typography, or theme tokens
- Component visual hierarchy or DOM order
- Animation or transition styles
- Responsive breakpoints

If adapting code requires a visual change, **stop and ask the user** before proceeding. Do not make a judgement call on style — preserve it exactly as-is.

## Slice Rules — ALWAYS ACTIVE

**Before suggesting any code, read `execution-plan.md` to find the current task.**

Before starting any new slice:
1. **Read `backend/specs/DEPENDENCY_MAP.md`** — check which signatures to pull from prior slices.
2. **Write the spec first** (`backend/specs/sliceN_name.md`) and wait for sign-off before any code.
3. **Write tests before implementation** (TDD) — all tests must fail first, then be made green.
4. **Run the full test suite after every slice** — not just the new tests. Fix any regressions before moving on.
5. **Never edit an already-applied migration** — schema changes go in a new migration file (additive only).
6. **Update `backend/specs/DEPENDENCY_MAP.md` after completing any new slice** — add every new service function, tool, or pattern the slice exposes so future slices can find and reuse them. This is not optional.

## Architecture Decision Records (ADR)

Any decision that deviates from `docs/architecture.md` or introduces a new architectural pattern must be recorded as an ADR. See `docs/adr/README.md` for format and existing records.

## Engineering Principles — ALWAYS ACTIVE

Before designing any solution, consider:

1. **Multiple engineers build this.** Any engineer should be able to clone the repo,
   follow the setup steps, and be productive. Never assume the person reading the code
   is the person who wrote it.

2. **A different set of engineers operates this.** The person troubleshooting a 2am
   incident may have never seen this codebase. Skills, runbooks, and error messages
   must guide a capable but unfamiliar engineer to the root cause without hand-holding
   from the original author.

3. **Configuration over hardcoding.** URLs, thresholds, credentials, and feature flags
   belong in configuration files or environment variables — never hardcoded in
   application code, skill files, or specs. If a value could change per environment,
   per deployment, or per engineer, it must be configurable. Use sensible defaults for
   values that are stable but overridable; require explicit configuration only for
   secrets and environment-specific values.

4. **Avoid technical debt — legacy fallbacks are a last resort.** When a modern standard
   fails, diagnose and fix the root cause first. Only fall back to a legacy approach
   (CommonJS, looser types, etc.) after exhausting all other paths. Document why when you do.

## Design Philosophy — Work Backwards From the User

Before designing or implementing any feature, ask: **who is the customer using this, and what do they need?**

Put the persona first. What does a customer trying to place an order, make a reservation, or submit a catering enquiry actually need? Design the API contract and UI around their journey — not around what is easy to implement.

This applies to: API design, field naming, validation rules, error messages shown to users, and UI flow.

## Pair Programming Rules — ALWAYS ACTIVE

The user is a new engineer learning Python by building this project. These rules apply to every coding task, no exceptions.

- **Never write code unprompted.** Always explain what you are about to suggest and why, then wait for the user to write it.
- **One piece at a time.** Suggest one function, one class, or one block — never a whole file at once.
- **Explain every meaningful line.** When suggesting code, describe what it does in plain English before or after.
- **Encourage the user to type.** Your role is to guide, not to implement. Ask "can you write that part?" before offering it.
- **No assumed knowledge.** Explain concepts (e.g. what a Pydantic validator is) before using them.
- **Boilerplate is fine to write directly** (imports, config, file scaffolding). Focus the user's energy on the meaningful logic.
- **If you catch yourself writing a full implementation — stop.** Break it into steps and guide instead.

## Performance Rules (Token Saving)
- Never read entire folders unless explicitly requested.
- Prefer git diff to detect changes.
- Avoid opening large files unnecessarily.
- Work file-by-file.

## Code Quality Rules

### File Size — HARD LIMIT
- **No single file may exceed 500 lines.** This is a hard limit, not a guideline.
- If a file approaches 400 lines, proactively split it before it grows further.
- **Never generate an entire feature or app in one file.** Every feature must be broken into multiple files with clear responsibilities.

## Migration Command Behavior
When user says:
"Migrate latest Lovable changes"

You MUST:
1. Run git diff against latest lovable_project commit.
2. Identify changed files only.
3. Migrate incrementally.
4. Confirm migrated file list before proceeding.

## Coding Best Practices

### General
- No magic numbers or hardcoded strings — use constants or config files.
- Keep functions small and single-purpose (max ~40 lines per function).
- Use meaningful, descriptive names for variables, functions, and files.
- Avoid deeply nested code — prefer early returns and guard clauses.
- Delete dead code; do not comment it out.

### Comments
- Comment the **WHY**, never the WHAT. Code already says what it does — a comment restating it is noise.
- Add a comment only when a competent engineer reading cold would be confused or make a wrong assumption without it: a non-obvious value, a hidden constraint, a subtle invariant, or a workaround that looks like it could be simplified but can't.
- Format: short inline comment on the relevant line — `# reason why, not what`.

### API & Services
- All API calls go through a dedicated service layer (not directly in components).
- Validate inputs at API boundaries.
- Return consistent response shapes (e.g., `{ data, error, status }`).
- Never expose sensitive keys or credentials in frontend code.

### Security
- Sanitize all user inputs before rendering or storing.
- Use environment variables for secrets — never hardcode them.
- Apply authentication middleware to all protected routes.
- Follow least-privilege principle for database queries.

### Testing
- Write tests for all service-layer functions.
- Use descriptive test names: `it("should return 404 when item not found")`.
- Mock only at system boundaries (HTTP, DB); never mock internal logic.
- Never hardcode values in tests that can become invalid over time or drift from the source of truth:
  - **Dates** — compute dynamically (e.g. `date.today() + timedelta(days=60)`)
  - **Prices and config values** — read from seed data constants or query the DB; never assume a specific dollar amount
  - **Reference data** (zip codes, item IDs) — define as named constants at the top of the test file with a comment pointing to the seed file, so drift is obvious

### Git & Build
- Never commit with `--no-verify` to bypass hooks.
- Never commit `.env` files, secrets, or API keys.
- Keep commits small and focused on one concern.
- **Never use `git add -A` or `git add .`** — always stage files explicitly by name.
- **If a commit touches more than 3–4 files, stop and split it.** Each commit should be reviewable in under 2 minutes. A new feature touching schema + resolver + types + test is fine; docs + unrelated hooks + config in one shot is not.
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
- Technology-specific pre-commit checklists are in `src/CLAUDE.md` (frontend) and `backend/CLAUDE.md` (backend).
