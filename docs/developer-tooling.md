# Developer Tooling

**Last updated:** 2026-04-21
**Reference from:** `execution-plan.md` — Developer Tooling track

This document covers the developer tooling layer: pre-commit hooks, local dev setup, and the Claude Code skill system that guides requirements, design, spec, and review workflows.

---

## 1. Pre-Commit Hooks

### Frontend (Husky + lint-staged)
- **Tool:** Husky 9.x + lint-staged 16.x
- **Triggers on:** staged `.ts` / `.tsx` files
- **Checks:** ESLint (auto-fix) + Prettier (auto-format)
- **Config:** `.husky/pre-commit`, `package.json` → `lint-staged`
- **Status:** ✅ Done 2026-04-21

### Backend (pre-commit framework)
- **Tool:** pre-commit framework
- **Triggers on:** staged `backend/**` Python files
- **Checks:** Black (format check, line length 88) + Flake8 (lint, `--extend-ignore=E203,E501`)
- **Config:** `.pre-commit-config.yaml`
- **Status:** ✅ Done 2026-04-21

### Setup requirement for new engineers
New engineers must run `pre-commit install` after cloning. See `README.md` → Pre-Commit Hooks section.

---

## 2. Local Dev Setup

- **README.md** covers: prerequisites, credentials, backend setup, frontend setup, pre-commit hooks, verification checklist
- **Agent-specific note:** agents must check `backend/.env` is populated before proceeding; stop and report missing variables if not
- **Status:** ✅ Done 2026-04-21

---

## 3. CI Strategy

| Layer | What runs | When |
|---|---|---|
| Pre-commit (local) | Lint + format only | Every commit |
| CI (GitHub Actions) | Full test suite: pytest + RTL + Vitest | On PR open/push |

Tests are NOT run pre-commit — they run in CI on PR. This keeps local commits fast and puts test enforcement at the PR gate where a human reviews anyway.

**Status:** Pre-commit ✅ Done | CI pipeline ⏳ Pending

---

## 4. Claude Code Skills

Skills are stored in `.claude/skills/` and committed to the repository so all engineers and agents share the same workflow.

### Skill: `/requirements`
- **Purpose:** Collaborative PM-style requirements writing
- **Output:** `docs/requirements/[feature-name].draft.md` → `[feature-name].md` on sign-off
- **Guardrails:** ambiguity detection, third-party cost flagging, security/compliance triggers, draft/sign-off gate
- **Template:** `.claude/skills/requirements/template.md`
- **Status:** ✅ Done 2026-04-21

### Skill: `/review`
- **Purpose:** Codebase review before any new feature is designed or implemented
- **Output:** Structured report in conversation (entities, endpoints, state machines, test gaps, reuse opportunities, conflicts, recommendations)
- **Called by:** other skills (requirements, design, spec) and standalone
- **Recommendations are advisory** — human decides what to act on
- **Status:** ✅ Done 2026-04-21 — ⏳ Not yet tested end-to-end

### Skill: `/design` ⏳ Pending
- **Purpose:** Translate approved requirements into system design (API contracts, data model, component structure)
- **Gate:** Reads approved requirements doc + calls `/review` before drafting
- **Output:** `docs/design/[feature-name].draft.md` → `[feature-name].md` on sign-off

### Skill: `/spec` ⏳ Pending
- **Purpose:** Write per-slice technical spec an engineer implements against
- **Gate:** Reads approved design doc + calls `/review` before drafting
- **Output:** `specs/[sliceN_name].draft.md` → `[sliceN_name].md` on sign-off

### Skill: `/execution-plan` ⏳ Pending
- **Purpose:** Break approved design into ordered slices with dependencies
- **Output:** New slice entries added to `execution-plan.md`

---

## 5. Feedback Loop — Phase Gates

Each phase requires explicit human sign-off before the next phase begins:

```
Requirements (approved) → Design → Design (approved) → Spec → Spec (approved) → Build → PR → Human review → Deploy
```

- Skills enforce this by saving drafts and not finalising until PM/engineer explicitly signs off
- `/review` runs at the start of each skill to surface existing code, conflicts, and reuse opportunities before any drafting

---

## 6. Traceability

| From | To | How |
|---|---|---|
| Requirements (REQ-XXX-NNN) | Design decisions | Design doc references REQ IDs |
| Design decisions | Spec sections | Spec references design decisions |
| Spec acceptance criteria | Tests | Tests reference AC IDs |
| Tests | CI | CI enforces test pass on every PR |

For legacy features with no documentation: code, DB schema, and migrations are the source of truth. `/review` reads these directly — it does not assume docs exist.

---

## 7. Open Items

| # | Item | Status |
|---|---|---|
| 1 | Test `/review` skill end-to-end against a real domain | ⏳ Next |
| 2 | Wire `/review` call into `/requirements` skill | ⏳ Pending test result |
| 3 | Build `/design` skill | ⏳ Pending |
| 4 | Build `/spec` skill | ⏳ Pending |
| 5 | Build `/execution-plan` skill | ⏳ Pending |
| 6 | CI pipeline (GitHub Actions) for pytest + RTL + Vitest | ⏳ Pending |
| 7 | Write unit + integration tests for menu slice (backend + frontend) | ⏳ Pending |
