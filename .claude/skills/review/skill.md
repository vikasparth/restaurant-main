# Review Skill

You are performing a codebase review before a new feature is designed or implemented. Your job is to surface what already exists in the relevant domain so the calling skill or human can make informed decisions — not assumptions.

This skill is intentionally read-only. It reports. It does not implement, decide, or block.

---

## Inputs

### When called by another skill
Domain and intent are already in the conversation context. Use them directly — do not re-ask.

### When called standalone
Ask the user:
1. "What domain or feature area are you working in? (e.g. menu, reservations, orders, auth, catering)"
2. "In one sentence — what are you about to build or change?"
3. "Do you have any existing documentation for this domain? If so, where does it live?"

---

## What to Read

Once you have the domain and intent, search the codebase using the domain keyword as a filter. Read files — do not guess their contents.

### Backend
- `backend/models/` — glob for all model files, grep for domain keyword, read matching files
- `backend/services/` — grep for domain keyword, read matching service files
- `backend/routers/` — grep for domain keyword, read matching route files
- `backend/alembic/versions/` — grep for domain keyword in migration files; note schema changes
- `backend/tests/` — grep for domain keyword; note what is and is not tested

### Frontend
- `src/services/` — grep for domain keyword; read matching service files
- `src/components/` — grep for domain keyword; note which components touch this domain
- `src/hooks/` — grep for domain keyword

### Shared Utilities and Reusable Modules
- `src/lib/`, `src/utils/`, `backend/utils/`, `backend/core/` — grep for domain keyword and related concepts
- Note any shared utilities, base classes, mixins, hooks, or helpers that are domain-agnostic but could be relevant

### Dependency Map
- Always read `backend/specs/DEPENDENCY_MAP.md` — it tracks every service function, tool, and pattern exposed by completed slices. This is the most reliable record of what has been intentionally built.

### Documentation
- If the user provided doc locations, read those first
- Also run a broad search: grep for the domain keyword across all `.md` files in the repo
- Note each doc found, what it covers, and its status (Draft / Approved / no status)

---

## Output — Review Report

Produce the report below in full in the conversation. Both the calling skill and the human must see it before any drafting begins.

All recommendations (reuse, refactor) are advisory — the human decides what to act on.

---

## Codebase Review: [Domain]

**Intent:** [what you are about to build, one sentence]

### Existing Entities
| Entity | Key Fields | Location |
|---|---|---|
| [model name] | [field: type, ...] | [file:line] |

### Existing API Endpoints
| Method | Path | Handler | Notes |
|---|---|---|---|
| [GET/POST/...] | [/path] | [function name] | [brief description] |

### Existing State Machines
[List entity state transitions found in service logic — or N/A]

### Test Coverage
| Test File | What Is Covered | Gap |
|---|---|---|
| [file] | [scenarios tested] | [what is missing] |

### Existing Documentation
| Doc | Covers | Status |
|---|---|---|
| [file path] | [what it covers] | Draft / Approved / Missing |

### Reuse Opportunities
> Existing code, components, hooks, or utilities the new feature could reuse rather than rebuild.

| Item | Location | How it could be reused |
|---|---|---|
| [function / component / hook] | [file:line] | [suggested reuse] |

### Potential Conflicts with Intent
> Anything in existing code that could conflict with, duplicate, or constrain what is being built.

| Conflict | Location | Risk | Notes |
|---|---|---|---|
| [description] | [file:line] | High / Medium / Low | [context] |

### Recommendations
> Advisory only — the human decides what to act on.

| Type | Description | Benefit |
|---|---|---|
| Refactor | [what to change and where] | [why it would help] |
| Reuse | [use X instead of building Y] | [avoids duplication] |
| Caution | [something to be careful about] | [risk if ignored] |

### Constraints the New Feature Must Respect
- [hard constraint from existing code, schema, or migration]

---

## Behaviour Rules

- **Read before reporting.** Never guess what exists — open the files and read them.
- **If nothing is found in a section**, say so explicitly: "Nothing found in [location] for this domain."
- **Flag conflicts clearly.** Use the conflicts table — never bury a conflict in a paragraph.
- **All file references must include line numbers** so the human can navigate directly.
- **Recommendations are advisory.** Label them clearly. Never block the calling skill or the human from proceeding.
- **Do not proceed past the report.** The calling skill or human decides what happens next.
