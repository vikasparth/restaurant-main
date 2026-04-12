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
1. **Read `specs/DEPENDENCY_MAP.md`** — check which signatures to pull from prior slices.
2. **Write the spec first** (`specs/sliceN_name.md`) and wait for sign-off before any code.
3. **Write tests before implementation** (TDD) — all tests must fail first, then be made green.
4. **Run the full test suite after every slice** — not just the new tests. Fix any regressions before moving on.
5. **Never edit an already-applied migration** — schema changes go in a new migration file (additive only).

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

### Git & Build
- Never commit with `--no-verify` to bypass hooks.
- Never commit `.env` files, secrets, or API keys.
- Keep commits small and focused on one concern.
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
- Technology-specific pre-commit checklists are in `src/CLAUDE.md` (frontend) and `backend/CLAUDE.md` (backend).
