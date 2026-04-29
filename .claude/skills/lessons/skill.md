# Lessons Skill

You are helping the user record a strategic gap, guardrail, or best practice they identified
in your approach. Capture it cleanly in `docs/learning-log.md`. Each entry records what the
AI was doing wrong, why it mattered, and the rule created to prevent recurrence.

## Conversation Flow

Ask these questions **one at a time**. Do not ask the next until the user has answered.

**Step 1 — What happened**
"What did you catch? In one or two sentences, what was I doing or recommending that you pushed back on?"

**Step 2 — Why it was wrong**
"What's the problem with that approach — what would go wrong if it went unchallenged?"

**Step 3 — The principle or guardrail**
"What rule, principle, or guardrail came out of this? Was it added somewhere (CLAUDE.md, a skill, a script), or is it an informal principle you want to remember?"

## Drafting

Once you have all three answers, draft the entry:

```
## [Title — the pattern or gap, not the specific incident]

[One to two paragraphs: what the AI was recommending, what the user identified, how it connects
to a broader engineering concern. No bullet points. Written for a future reader who needs context,
not a literal incident report.]

**[Principle enforced / Guardrail created]:** [The rule in one sentence.]
```

Show the draft and ask: "Does this read right, or would you change anything?"
**Do not write to the file until the user approves.**

## Writing

Append the approved entry to `docs/learning-log.md` — after all existing entries, separated
by a blank line before `##`. Do not modify any existing entries.

Confirm with: "Logged."

## Title and Body Rules

- Title captures the pattern, not the incident. "Hardcoding — validator was domain-specific" not "Bug in validate-schema.js on 25 April."
- Body reads cold. A reader who wasn't in this conversation should understand both the mistake and the principle.
- Close with the principle in bold: `**Principle enforced:**` for an existing rule, `**Guardrail created:**` for a new one, or `**Principle enforced / Guardrail created:**` if both apply.
