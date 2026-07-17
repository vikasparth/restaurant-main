---
paths:
  - "agents/**/*.py"
---

## Agent Structure Rules

- Every agent lives in its own file: `agents/<name>_agent.py`.
- Every agent exposes a single `run() -> str` entry point that returns a YAML finding string.
- The agentic loop must be bounded by a max turns constant from `agents/config.py` — never an unbounded `while True`.
- Partial fallback YAML (`status: partial`) must be returned — never raise or return `None` when the turn budget is exhausted.

## Token Efficiency

- **Never pass raw API responses into LLM context.** Tool functions must extract only the fields the LLM needs to reason about — not the full response object.
- **Apply time windows to all list queries.** Fetch only recent data (e.g. last 1 hour for live issues). Stale data is noise that wastes tokens.
- **Limit list results to 3–5 items maximum.** The agent investigates one issue at a time — the orchestrator decides which one. Fetching 25 issues to let Claude pick one is the wrong design.
- **Trim stack traces to the essential fields only:** exception type, exception message, culprit file, and top 1–2 frames. Breadcrumbs, request headers, and framework frames must be dropped before returning.
- **Target under 5k tokens per agent run** on Haiku. If a run exceeds this, review tool result payloads first.
- **Trim fully-consumed tool results in agentic loops.** After each `client.messages.create()` call, shrink tool results whose content has been fully consumed and is not needed for future reasoning — e.g. a file read that Claude has already acted on. Replace with a short stub like `"[file read — content processed]"`. Do not trim results that a later turn may need to compare or reconcile. The API is stateless — every turn resends the full `messages` list, so large payloads left in place compound token usage; but trimming prematurely can break reasoning that depends on prior content.
