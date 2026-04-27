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

## TypeScript Interface Rules

- **Interfaces are compile-time only** — they do not affect the runtime payload. Changing a field name in an interface does not change what gets sent over the network.
- **The actual payload is built in the form component or service** — that is where field names must be correct.
- **TypeScript cannot validate against the backend Pydantic model** — if an interface drifts from the backend schema, TypeScript will not catch it. The backend's `extra="forbid"` is the runtime safety net.
- **Never write frontend interfaces by hand** — in Phase 2, generate them from `openapi.json` using codegen so frontend types always mirror the backend contract exactly.
- **For request models: explicitly type the payload object** as the interface type so TypeScript performs excess property checking:

```ts
// ✅ TypeScript checks the object against ReservationCreateRequest
const payload: ReservationCreateRequest = {
  customer_name: name,
  customer_phone: phone,
  ...
};

// ❌ no type — TypeScript cannot catch extra or missing fields
const payload = {
  customer_name: name,
  customers_phone: phone,  // typo — not caught
};
```

## React / UI
- One component per file.
- Keep components under 150 lines; extract sub-components if needed.
- No business logic inside UI components — delegate to services/hooks.
- Use custom hooks to encapsulate stateful logic.
- Avoid inline styles; use Tailwind classes or CSS modules consistently.

## Error Logging — Required in Every Catch Block
Every catch block that handles a user-facing operation must log to Sentry via `logger.ts`.

```ts
import { logger } from "@/lib/logger";

} catch (e) {
  logger.error("[orders] failed to create order", e);
  toast.error("Something went wrong. Please try again.");
}
```

Rules:
- Message format: `[feature] failed to <operation>` — same pattern as the backend
- Always pass the original exception as the second argument — Sentry needs it for the stack trace
- Only log to Sentry for **unknown** errors — expected business errors (e.g. zip not covered) are handled in the UI and do not need Sentry
- In development `logger.error` calls `console.error`; in production it calls `Sentry.captureException()`

## Accessibility (ARIA) — Required on Every Page
Every page and component must follow these rules. Accessible names serve three purposes: screen readers, readable Sentry breadcrumbs, and Playwright E2E test selectors.

> `src/main.tsx` has a `beforeBreadcrumb` hook that reads `aria-label` then `id` for all UI events. Without these attributes, Sentry breadcrumbs fall back to unreadable Tailwind class selectors. ARIA must be wired for breadcrumbs to be useful.

| Element | Rule |
|---|---|
| `<input>` / `<select>` / `<textarea>` with a visible label | Use `htmlFor`/`id` pair — visual proximity alone is not sufficient |
| `<input>` / `<select>` without a visible label | Add `aria-label` |
| `<button>` with static descriptive text (e.g. "Submit") | No `aria-label` needed — text is the accessible name |
| `<button>` with dynamic text (e.g. loading states: "Place Order" / "Placing Order…") | Add `aria-label` with the stable name — text content changes but the label stays fixed |
| `<button>` whose text is ambiguous without context (e.g. "Remove") | Add `aria-label` to make it specific (e.g. `aria-label="Remove Butter Chicken"`) |
| `<button>` with icon only | Add `aria-label` |
| Toggle buttons that communicate active state | Add `aria-pressed={boolean}` |
| Decorative icons (Lucide or otherwise) | Add `aria-hidden="true"` |

**Never** use `data-sentry-element` or `data-testid` as substitutes — fix the underlying naming instead.

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
