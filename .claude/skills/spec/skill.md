# Spec Writing Skill

You have been asked to write a spec for the next slice in the execution plan.

A spec is the contract between the execution plan and the implementation. It defines the
signature, return shape, filtering pipeline, exit conditions, and TDD test plan before a
single line of implementation code is written. No implementation may begin until the spec
is signed off.

---

## Step 1 — Gather Context

Ask the user **one question at a time** in this order. Stop after each and wait for the answer.

1. **Which execution plan file should I read?** (e.g. `execution-plan.md`, `docs/engineering-practices/agent-execution-plan.md`)
2. **Which architecture document should I reference?** (e.g. `docs/architecture.md`, `docs/engineering-practices/agent-architecture.md`)
3. **Which layer is this spec for?** — agents / backend / frontend / other

Once you have all three answers, read the execution plan to find the current task. Use the
index (first 30 lines) to find the relevant section, then offset + limit to read only that
section. Extract the task ID, description, and `Arch sections:` field.

State these back to the user before proceeding.

---

## Step 2 — Load the Layer Profile

Read the profile for the detected layer from `.claude/skills/spec/profiles/{layer}.md`.

The profile defines:
- Which dependency map to read
- The spec template — sections, rules, and format specific to this layer
- File naming conventions
- Which test skills to invoke after sign-off (the `test_skills` list)

Follow the profile exactly for the remainder of this skill.

---

## Step 3 — Read Architecture Sections

Using the architecture document the user provided in Step 1, grep for each section name from:

1. The task row's `Arch sections:` field
2. The profile's "Always read" list

Use grep → line number → offset + limit for each section. Never read the full document.

---

## Step 4 — Read the Dependency Map

Read the dependency map specified in the profile. Scan for:

- Functions or helpers with the same responsibility as the new slice
- Existing STATUS_ constants — never define one that already exists
- Shared utilities the new slice should import rather than redefine

Note every reusable item. The spec must reference these rather than inventing new ones.

---

## Step 5 — Write the Spec

Using the profile template, generate the spec file at the path the profile specifies.

Rules that apply to every layer:
- Section names are the contract — use the exact headings from the profile; do not rename them
- Every spec header must include `Architecture doc sections:` listing the sections read in Step 3
- Every configurable value (limits, model names, URLs) must reference a config constant — never a literal
- Private helper functions must be listed — these become the patch targets for tests

Present the completed spec to the user and ask:
> "Does this spec look right? Any changes before sign-off?"

Do not proceed until the user explicitly approves.

---

## Step 6 — Update Supporting Documents

Once signed off:

1. Update the execution plan file — change the task status to `🔄 In Progress`
2. Update the Current Focus line to reflect the new task

---

## Step 7 — Generate Test Coverage

Read the `test_skills` list from the profile.

**If `test_skills` has entries:** invoke each skill in order, passing the spec file path as
context. Each skill produces its own test plan for its domain (API integration, frontend
unit tests, data validation, etc.).

**If `test_skills` is empty:** generate a unit test plan directly from the spec content.
Use the signature, return shape, filtering pipeline, and exit conditions to derive test
cases. Cover at minimum: happy path, edge cases, and each distinct return status. Present
the plan and ask:
> "Does this test coverage look complete, or are there scenarios I've missed?"

Wait for the user's confirmation before marking the spec done.

The goal is that every spec always leaves with a confirmed test plan — there is no path
through this skill that produces a spec with no tests defined.
