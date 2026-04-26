# Lessons Skill

You are helping the user record a strategic gap, guardrail, or best practice they identified in your approach. Your job is to capture it cleanly in `docs/learning-log.md`.

## Purpose

This log is a personal revision reference for the user — not a task list, not an issue tracker. Each entry captures:
- A case where the user identified a flaw in the AI's approach
- Why that matters (the principle behind the pushback)
- The guardrail or rule created to prevent recurrence

---

## Conversation Flow

Ask these questions **one at a time** — never all at once. Build on the previous answer before asking the next.

### Step 1 — What happened
Ask: "What did you catch? In one or two sentences, what was I doing or recommending that you pushed back on?"

### Step 2 — Why it was wrong
Ask: "What's the problem with that approach — what would go wrong if it went unchallenged?"

### Step 3 — The principle or guardrail
Ask: "What rule, principle, or guardrail came out of this? Was it added somewhere (CLAUDE.md, a skill, a script), or is it an informal principle you want to remember?"

---

## Drafting

Once you have all three answers, draft the entry using this format:

```
## [Title — the pattern or gap, not the specific incident]

[One to two paragraphs: what the AI was recommending, what the user identified, how it connects
to a broader engineering concern. No bullet points. Written for a future reader who needs context,
not a literal incident report.]

**[Principle enforced / Guardrail created]:** [The rule in one sentence — what a future engineer
(or AI) should do instead.]
```

Show the draft. Ask: "Does this read right, or would you change anything?"

**Do not write to the file until the user approves.**

---

## Writing

Once the user approves, append the new entry to `docs/learning-log.md`:
- Add after all existing entries, separated by a blank line before `##`
- Do not modify any existing entries

Confirm with: "Logged."

---

## Behaviour Rules

- **One question at a time.** Never ask Step 2 and Step 3 together.
- **Draft before writing.** Always show the entry and get approval first.
- **Title captures the pattern, not the incident.** "Hardcoding — validator was domain-specific" not "Bug in validate-schema.js on 25 April."
- **Body reads cold.** A reader who wasn't in this conversation should understand both the mistake and the principle.
- **Close with the principle in bold.** Use `**Principle enforced:**` for a rule that already existed, `**Guardrail created:**` for a new one, or `**Principle enforced / Guardrail created:**` if both apply.
