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

### Feature Organisation
Organise code by feature, not by type. Each feature folder should contain its own components, hooks, services, and types:

```
src/
  features/
    menu/
      components/       # UI components for this feature
      hooks/            # custom React hooks
      services/         # API calls, business logic
      types.ts          # TypeScript types/interfaces
      index.ts          # public exports only
    orders/
    reservations/
    auth/
  shared/
    components/         # reusable UI primitives
    utils/
    constants/
  pages/                # route-level page components only
  lib/                  # third-party wrappers (e.g. axios instance, supabase client)
```

- Never put business logic directly in page files.
- `pages/` files should only compose feature components, nothing else.
- Shared utilities go in `shared/` — never duplicated across features.

## Backend Expectations
- Backend lives only in main_project.
- Do not generate backend code inside lovable_project.

### Authentication — Required Everywhere
- **Every protected route MUST have authentication middleware.** No exceptions.
- Apply auth guards on:
  - All admin pages and dashboard routes
  - All API routes that read or write data
  - Any route that involves user-specific data (orders, reservations, profiles)
- Use role-based access control (RBAC) where different user types exist (e.g. admin, staff, customer).
- Auth tokens must be stored securely (httpOnly cookies preferred over localStorage).
- Always validate the session/token on the server side — never trust client-side auth state alone.
- Add an auth layer to the API service wrapper so every request automatically includes credentials.

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

### TypeScript / JavaScript
- Use TypeScript strict mode (`"strict": true`).
- Prefer `const` over `let`; never use `var`.
- Use explicit types — avoid `any`.
- Use named exports over default exports for better refactoring.
- Handle all promise rejections and async errors.

### React / UI
- One component per file.
- Keep components under 150 lines; extract sub-components if needed.
- No business logic inside UI components — delegate to services/hooks.
- Use custom hooks to encapsulate stateful logic.
- Avoid inline styles; use Tailwind classes or CSS modules consistently.

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

### Git & Build — Pre-Commit Checklist
Before every commit, ALL of the following must pass:

1. **TypeScript compile** — `tsc --noEmit` (zero type errors)
2. **Lint** — `eslint . --max-warnings 0` (zero warnings allowed)
3. **Format check** — `prettier --check .` (no unformatted files)
4. **Build** — `npm run build` must complete without errors
5. **Tests** — `npm test -- --watchAll=false` (no failing tests)

- Never commit with `--no-verify` to bypass hooks.
- Never commit `.env` files, secrets, or API keys.
- Keep commits small and focused on one concern.
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
