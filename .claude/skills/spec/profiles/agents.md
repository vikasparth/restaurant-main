# Spec Profile — Agents Layer

This profile is loaded by the `/spec` skill when the layer is `agents`.
It defines the structure and lookup pointers for an agents-layer spec.
Content for each section is derived from reading the architecture doc — not from this profile.

---

## Profile Config

```
dependency_map:  agents/specs/DEPENDENCY_MAP.md
spec_output_dir: agents/specs/
test_skills:     ask — only include api-integration-tests if the slice calls an external HTTP API
```

---

## Always Read Architecture Sections

In addition to the task's `Arch sections:` field, always read:

- `Agent Catalog` — confirms the agent's role and position in the pipeline
- `Principles` — token efficiency, PII, injection guard rules

---

## Required Spec Sections (in this order)

1. **What this slice builds** — one paragraph; what it does and what it returns
2. **Signature** — derived from architecture doc and dependency map
3. **Guardrails consumed** — table; derived from architecture doc query contract
4. **Return Shape** — derived from the findings schema section in architecture doc
5. **Implementation Rules** — numbered; derived from architecture doc + dep map reuse check
6. **Filtering Pipeline** — ordered steps; derived from architecture doc query contract (omit if not applicable)
7. **Exit Conditions** — table: status | trigger | orchestrator action; derived from architecture doc
8. **Private Helper Functions** — stubs only; one-line comment per function describing its contract
9. **TDD Test Plan** — filled in by test skill in Step 7
10. **Files Touched** — table of every file this slice creates or modifies
11. **Acceptance Criteria** — checklist; include current test suite count

---

## Layer-Specific Rules

Three rules that apply to every agents-layer spec regardless of agent type:

1. **Status constants** — check `agents/specs/DEPENDENCY_MAP.md` before defining any new STATUS_ constant; import existing ones from `agents/config.py`
2. **Observability** — `record_agent_run` must appear in the spec's implementation rules; it is called before every return path
3. **Imports** — no cross-feature imports; shared helpers come only from `patterns.py`, `sentry_utils.py`, or `config.py`
