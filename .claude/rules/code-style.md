## File Size — HARD LIMIT
- **No single file may exceed 500 lines.** This is a hard limit, not a guideline.
- If a file approaches 400 lines, proactively split it before it grows further.
- **Never generate an entire feature or app in one file.** Every feature must be broken into multiple files with clear responsibilities.

## General
- No magic numbers or hardcoded strings — use constants or config files.
- Keep functions small and single-purpose (max ~40 lines per function).
- Use meaningful, descriptive names for variables, functions, and files.
- Avoid deeply nested code — prefer early returns and guard clauses.
- Delete dead code; do not comment it out.
- **Never import from one feature module into another.** If two modules need the same code, extract it into a shared common file first. Cross-feature imports create hidden dependencies, hurt discoverability, and compound as more modules are added.

## Comments
- Comment the **WHY**, never the WHAT. Code already says what it does — a comment restating it is noise.
- Add a comment only when a competent engineer reading cold would be confused or make a wrong assumption without it: a non-obvious value, a hidden constraint, a subtle invariant, or a workaround that looks like it could be simplified but can't.
- Format: short inline comment on the relevant line — `# reason why, not what`.
- **In pair programming sessions** — add a WHY comment to any non-obvious code snippet shared in chat. Keep it to one line, minimum words. If the code speaks for itself, no comment needed.

### Config and Infrastructure Files — ALWAYS COMMENT
**GitHub Actions workflows, Docker files, CI configs, and any infrastructure-as-code MUST include WHY comments.** These files are especially opaque to new engineers — the intent behind each decision is rarely obvious from the syntax alone.

For every non-trivial block in a config file, explain:
- **Why this file exists** — what problem it solves and what would break without it.
- **Why this trigger/condition** — e.g. why only `main` and not feature branches.
- **Why this specific value or flag** — e.g. why `fetch-depth: 0` instead of the default shallow clone.

Do not just describe what a step does — explain the reasoning a new engineer would need to make a safe change or diagnose a failure at 2am.
