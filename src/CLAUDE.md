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

## Gateway Error UX — Handled Globally

Network and timeout errors are handled globally in `src/lib/apolloClient.ts` via an Apollo `onError` link. **Do not add timeout or network error handling in individual pages or hooks** — it is already wired.

What the global handler does:
- `503` / `504` on a **mutation** → "Your request timed out — we may not have received it. Please try again or contact us directly."
- `503` / `504` on a **query** → "Taking longer than expected — the server may be starting up. Please try again in a moment."
- Any other network error → "Connection problem — please check your connection and try again."

GraphQL errors (business logic errors returned in the response body) are **not** handled here — catch and display those in the component.

## Pre-Commit Checklist (Frontend)
Before every commit touching frontend code, ALL of the following must pass:

1. **TypeScript compile** — `npx tsc --noEmit -p tsconfig.app.json` (zero type errors — always use `-p tsconfig.app.json`, not bare `tsc --noEmit` which reads the root config and misses app errors)
2. **Lint** — `eslint . --max-warnings 0` (zero warnings allowed)
3. **Format check** — `prettier --check .` (no unformatted files)
4. **Build** — `npm run build` must complete without errors

## Migration Checklist
After every migration batch from Lovable, ALL of the following must pass before committing:

1. **TypeScript compile** — `npx tsc --noEmit -p tsconfig.app.json` (zero type errors)
2. **Check for missing files** — `diff <(find lovable/src -type f | sort) <(find src -type f | sort)` to catch hooks, components, or utilities that were not copied over
3. **Verify imports resolve** — any new component that imports from `@/hooks/*` or `@/lib/*` must have those files present in `src/`
