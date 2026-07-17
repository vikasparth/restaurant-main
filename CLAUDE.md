# Project Rules — Restaurant Management System

## Project Architecture

Three-layer restaurant management system ("Aap ki Rasoi"):

- **Frontend** (`src/`) — React 18 + TypeScript + Vite, Apollo Client (GraphQL). Feature-based structure under `src/features/`. Rules: `src/CLAUDE.md`.
- **Backend** (`backend/`) — Python/FastAPI REST API. Routes → Services → DB. Rules: `backend/CLAUDE.md`.
- **Agents** (`agents/`) — Anthropic-powered monitoring agents. Each agent is `agents/<name>_agent.py` with a single `run() -> str` entry point. Uses its own `.venv` — separate from the backend venv. Rules: `agents/CLAUDE.md`.

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
1. **Check the dependency map for your layer** — each layer (backend, agents, frontend) owns its own dependency map. Find it, check which signatures or patterns already exist, and reuse them before writing new ones.
2. **Write the spec first** and wait for sign-off before any code.
3. **Write tests before implementation** (TDD) — all tests must fail first, then be made green.
4. **Run the full test suite after every slice** — not just the new tests. Fix any regressions before moving on.
5. **Never edit an already-applied migration** — schema changes go in a new migration file (additive only).
6. **Update the dependency map for your layer after completing any new slice** — add every new function, tool, or pattern the slice exposes so future slices can find and reuse them. This is not optional.

## Architecture Decision Records (ADR)

Any decision that deviates from `docs/architecture.md` or introduces a new architectural pattern must be recorded as an ADR. See `docs/adr/README.md` for format and existing records.

## Cross-Document Traceability — ALWAYS ACTIVE

This project has three interlocking documents: architecture doc, execution plan, and per-task specs. The navigation primitive for a GenAI agent is **grep → offset+limit**, not hyperlinks. Section names are the stable keys that connect all three.

### Rules

1. **Section names are the contract.** Architecture doc section headings must not be renamed once referenced. They are the grep target for all downstream navigation.

2. **Execution plan task rows must include an `Arch sections:` field** listing the exact architecture doc section name(s) that govern the task. Example:
   ```
   **Arch sections:** `Render Agent Query Contract`, `Render Logs Findings Schema`
   ```

3. **Spec headers must include an `Architecture doc sections:` field** listing the same section names. This tells a GenAI agent which sections to read before writing any code.

4. **Navigation pattern — always use this, never read the full doc:**
   - Grep the architecture doc for the section name → get line number
   - Read only that section using `offset` + `limit`

5. **Write-back pattern — when a new decision is made during a slice:**
   - Grep the architecture doc for the relevant section name → get line number
   - Read only that section
   - Update only that section
   - Never read or rewrite the full document

## Engineering Principles — ALWAYS ACTIVE

Before designing any solution, consider:

1. **Multiple engineers build this.** Any engineer should be able to clone the repo,
   follow the setup steps, and be productive. Never assume the person reading the code
   is the person who wrote it.

2. **A different set of engineers operates this.** The person troubleshooting a 2am
   incident may have never seen this codebase. Skills, runbooks, and error messages
   must guide a capable but unfamiliar engineer to the root cause without hand-holding
   from the original author.

3. **Check config before writing any hardcoded value in code.** Before using any model name, URL, threshold, limit, or credential as a literal in code: (1) check the relevant config file first; (2) if the value is not there, define it in config first; (3) then reference the constant. Every configurable value has exactly one home — its config file. Use typed config (enums, Pydantic `BaseSettings`) so the type checker enforces this automatically, not a human reviewer.

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
- **Large documents with a Table of Contents — read the index first (first ~30 lines), identify the relevant section's line number, then use `offset` + `limit` to read only that section.** Never read the whole file when an index exists.

## Migration Command Behavior
When user says:
"Migrate latest Lovable changes"

You MUST:
1. Run git diff against latest lovable_project commit.
2. Identify changed files only.
3. Migrate incrementally.
4. Confirm migrated file list before proceeding.

## Coding Best Practices

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
- **Never log or transmit PII or PHI data.** This includes customer names, emails, phone numbers, IP addresses, order history, and health-related dietary information. Applies to application logs, Sentry events, and any third-party service.
- **Every `Sentry.init()` call must include a `beforeSend` hook** that scrubs known PII/PHI fields (e.g. `customer_name`, `customer_email`, `customer_phone`) from the event payload before it is sent. This applies to all layers: frontend, backend, and gateway.

### Git & Build
- Never commit with `--no-verify` to bypass hooks.
- Never commit `.env` files, secrets, or API keys.
- Keep commits small and focused on one concern.
- **Never use `git add -A` or `git add .`** — always stage files explicitly by name.
- **If a commit touches more than 3–4 files, stop and split it.** Each commit should be reviewable in under 2 minutes. A new feature touching schema + resolver + types + test is fine; docs + unrelated hooks + config in one shot is not.
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
- Technology-specific pre-commit checklists are in `src/CLAUDE.md` (frontend) and `backend/CLAUDE.md` (backend).
