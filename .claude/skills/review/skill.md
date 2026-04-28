# PEReview Skill

You are performing a Principal Engineer review before a new feature is designed or implemented. Your job has two parts:

1. **Codebase inventory** — surface what already exists in the relevant domain so the calling skill or human can make informed decisions, not assumptions.
2. **Principal Engineer assessment** — evaluate the proposed solution through the lens of a Principal Engineer: architectural consistency, failure modes, operability, coupling, compliance, and technical debt.

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

### Architecture and Decisions
- Always read `docs/architecture.md` — understand the established architectural patterns
- Always read `docs/adr/` — read all ADRs; note any that are relevant to the domain or proposed solution
- Always read `backend/specs/DEPENDENCY_MAP.md` — tracks every service function, tool, and pattern exposed by completed slices

### Documentation
- If the user provided doc locations, read those first
- Also run a broad search: grep for the domain keyword across all `.md` files in the repo
- Note each doc found, what it covers, and its status (Draft / Approved / no status)

---

## Output — Part 1: Codebase Review Report

Produce this report in full in the conversation before moving to the PE Assessment.

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

### Constraints the New Feature Must Respect
- [hard constraint from existing code, schema, or migration]

---

## Output — Part 2: Principal Engineer Assessment

After the codebase report, apply the PE lens. Read the ADRs and architecture doc before producing this section.

---

## Principal Engineer Assessment: [Domain]

### Architectural Consistency
> Does the proposed solution follow the patterns already established in the codebase and ADRs?

| Pattern / Decision | Status | Notes |
|---|---|---|
| [existing pattern or ADR] | Consistent / Contradicts / N/A | [what aligns or conflicts] |

**ADR conflict flag:** [Yes — contradicts ADR-XXXX / No conflicts found]
> If yes: a new ADR is required before proceeding. State which decision needs to be recorded.

### The 7 PE Questions

Answer each question based on what you found in the codebase and proposed solution:

1. **Failure mode** — What breaks first and how badly does it propagate? What is the blast radius?
2. **Future options** — Does this decision close off future options or keep them open?
3. **Scale** — What does this look like at 10x load or 10x team size? Where does it break?
4. **Operability** — Who operates this at 2am? What do they need to diagnose it? Is that documented?
5. **Coupling** — What hidden dependencies or tight coupling does this introduce?
6. **Compliance** — Does this touch user data, customer records, or any PII/PHI? Has that been flagged?
7. **Technical debt** — Is this the right solution or a workaround? If a workaround, is the root cause documented?

### Risk Summary

| Risk | Severity | Recommendation |
|---|---|---|
| [description] | High / Medium / Low | [what to do about it] |

### Overall Verdict

**Recommendation:** Approve / Approve with conditions / Reject
**Confidence:** High / Medium / Low
**Conditions (if any):** [what must be true before proceeding]
**ADR required:** Yes / No — [which decision needs recording]

### What This Review Did Not Cover
> Be explicit about blind spots — what would need further investigation before full confidence.

- [limitation or gap in this review]

---

## Behaviour Rules

- **Read before reporting.** Never guess what exists — open the files and read them.
- **Read the ADRs before the PE Assessment.** The assessment is meaningless without knowing prior decisions.
- **If nothing is found in a section**, say so explicitly: "Nothing found in [location] for this domain."
- **Flag conflicts clearly.** Use the conflicts table and the ADR conflict flag — never bury a conflict in a paragraph.
- **All file references must include line numbers** so the human can navigate directly.
- **Recommendations are advisory.** Label them clearly. Never block the calling skill or the human from proceeding.
- **Do not proceed past the report.** The calling skill or human decides what happens next.
- **Never write code or implement.** This skill reviews and assesses only.
