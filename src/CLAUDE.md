# Frontend Rules — Restaurant Management System

## Feature Organisation
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

## TypeScript / JavaScript
- Use TypeScript strict mode (`"strict": true`).
- Prefer `const` over `let`; never use `var`.
- Use explicit types — avoid `any`.
- Use named exports over default exports for better refactoring.
- Handle all promise rejections and async errors.

## React / UI
- One component per file.
- Keep components under 150 lines; extract sub-components if needed.
- No business logic inside UI components — delegate to services/hooks.
- Use custom hooks to encapsulate stateful logic.
- Avoid inline styles; use Tailwind classes or CSS modules consistently.

## Pre-Commit Checklist (Frontend)
Before every commit touching frontend code, ALL of the following must pass:

1. **TypeScript compile** — `tsc --noEmit` (zero type errors)
2. **Lint** — `eslint . --max-warnings 0` (zero warnings allowed)
3. **Format check** — `prettier --check .` (no unformatted files)
4. **Build** — `npm run build` must complete without errors
