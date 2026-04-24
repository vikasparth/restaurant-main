# Feature Folder Migration Guide

**Convention:** Migrate one feature at a time to `src/features/[feature]/`. A feature is migrated when it is updated to use the GraphQL gateway — not before.

---

## Why Migrate at All

`src/CLAUDE.md` defines the target structure as feature-based (`src/features/[feature]/`). The current flat structure (`src/services/`, `src/types/`, `src/hooks/`) was inherited from the Lovable migration. Each feature moves to the correct structure when it is touched for GraphQL — no big bang migration.

---

## Target Structure Per Feature

```
src/features/[feature]/
  components/     ← UI components for this feature only
  hooks/          ← custom React hooks (e.g. useMenu.ts)
  services/       ← REST service calls (kept during GraphQL transition)
  types.ts        ← TypeScript types for this feature
  index.ts        ← public exports only
```

`src/pages/[Feature]Page.tsx` — stays in `pages/`. Page files only compose feature components, they never move into `features/`.

---

## Migration Steps

Run these steps in order. Do not commit until all steps pass.

### 1. Create the feature folder structure
```bash
mkdir -p src/features/[feature]/hooks
mkdir -p src/features/[feature]/services
mkdir -p src/features/[feature]/components
```

### 2. Move files with git mv (preserves history)
```bash
git mv src/services/[feature]Service.ts src/features/[feature]/services/[feature]Service.ts
git mv src/types/[feature].ts src/features/[feature]/types.ts
# move any feature-specific components from src/components/ if they exist
```

### 3. Update all imports
Search for old import paths and update to new locations:
```bash
grep -rn "from.*services/[feature]Service" src/ --include="*.ts" --include="*.tsx"
grep -rn "from.*types/[feature]" src/ --include="*.ts" --include="*.tsx"
```

Update each reference to point to the new path.

### 4. Create the GraphQL hook
Add `src/features/[feature]/hooks/use[Feature].ts` — wraps `useQuery`, returns `data`, `loading`, `error`.

### 5. Verify — zero errors before committing
```bash
npx tsc --noEmit -p tsconfig.app.json   # zero type errors
npm run build                            # build must pass
```

### 6. Commit
```bash
git add src/features/[feature]/ src/pages/[Feature]Page.tsx
git commit -m "refactor: migrate [feature] to src/features/ and add GraphQL hook"
```

---

## Rollback Plan

If anything breaks before committing:
```bash
git checkout -- src/
```

This reverts all unstaged changes to `src/` instantly. Since TypeScript compile and build run before committing, a broken state is never committed.

If a broken state was committed (should not happen if steps are followed):
```bash
git revert HEAD
```

---

## Feature Migration Status

| Feature | Status | Notes |
|---|---|---|
| menu | 🔄 In Progress | First migration — GraphQL hook being added |
| orders | ⏳ Pending | Migrate when Orders moves to GraphQL |
| reservations | ⏳ Pending | Migrate when Reservations moves to GraphQL |
| catering | ⏳ Pending | Migrate when Catering moves to GraphQL |
| auth | ⏳ Pending | Migrate when Auth moves to GraphQL |
