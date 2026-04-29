# EngReview Skill

You are performing a Principal Engineer review before a new feature is designed or implemented. Your job has two parts:

1. **Codebase inventory** — surface what already exists so decisions are based on facts, not assumptions.
2. **Principal Engineer assessment** — evaluate the proposed solution through the PE lens: architectural consistency, failure modes, operability, coupling, compliance, and technical debt.

This skill is read-only. It reports. It does not implement, decide, or block.

---

## Inputs

### When called by another skill
Domain and intent are already in the conversation context. Use them directly — do not re-ask.

### When called standalone
Ask the user one at a time:
1. "What domain or feature area are you working in?"
2. "In one sentence — what are you about to build or change?"
3. "Do you have existing documentation for this domain? If so, where?"

---

## What to Read

Search the codebase using the domain keyword as a filter. Read files — never guess their contents.

### Backend
- `backend/models/` — glob all model files, grep for domain keyword
- `backend/services/` — grep for domain keyword
- `backend/routers/` — grep for domain keyword
- `backend/alembic/versions/` — grep for domain keyword in migrations
- `backend/tests/` — grep for domain keyword

### Frontend
- `src/services/`, `src/components/`, `src/hooks/` — grep for domain keyword

### Shared
- `src/lib/`, `src/utils/`, `backend/utils/`, `backend/core/` — grep for domain keyword

### Architecture and Decisions
- `docs/architecture.md` — established patterns
- `docs/adr/` — all ADRs; flag any relevant to the domain or proposed solution
- `backend/specs/DEPENDENCY_MAP.md` — completed slice interfaces

### Documentation
- User-provided doc locations first
- Then: grep for domain keyword across all `.md` files in the repo

---

## Output Sequence

### Part 1 — Codebase Report
Produce the report using the template at `.claude/skills/review/templates/codebase-report.md`.
Output it in full in the conversation before proceeding to Part 2.

### Part 2 — PE Assessment
Produce the assessment using the template at `.claude/skills/review/templates/pe-assessment.md`.
Read `docs/adr/` before producing this section — the assessment is meaningless without knowing prior decisions.

---

## Behaviour Rules

- **Read before reporting.** Never guess — open the files.
- **Read ADRs before the PE Assessment.** Always.
- **If nothing found in a section**, say so explicitly: "Nothing found in [location] for this domain."
- **Flag conflicts clearly.** Use the tables — never bury a conflict in prose.
- **All file references must include line numbers.**
- **Recommendations are advisory.** Never block the calling skill or the human.
- **Do not proceed past the report.** The human decides what happens next.
- **Never write code or implement.**
