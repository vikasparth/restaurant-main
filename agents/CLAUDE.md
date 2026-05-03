# Agents Project Rules — Aap ki Rasoi

## Agentic Observability — ALWAYS ACTIVE

- **Every agent `run()` must call `record_agent_run()` before every return path** — observability is not optional and must be wired at the time the agent is built, not retrofitted later.
- Token usage (`input_tokens`, `output_tokens`) is available free on every Anthropic API response — never discard it. Accumulate `usage_by_turn` during the loop and pass it to `record_agent_run()`.
- **No separate Anthropic calls for observability data** — read token counts from existing responses only.
- Confidence must be recorded numerically (high=3, medium=2, low=1) so trends can be charted over time in Sentry.

## Agent Structure Rules

- Every agent lives in its own file: `agents/<name>_agent.py`.
- Every agent exposes a single `run() -> str` entry point that returns a YAML finding string.
- The agentic loop must be bounded by a max turns constant from `agents/config.py` — never an unbounded `while True`.
- Partial fallback YAML (`status: partial`) must be returned — never raise or return `None` when the turn budget is exhausted.

## Observability Wiring Checklist

Before marking any agent task done, verify:
- [ ] `usage_by_turn` list initialised before the loop
- [ ] `usage_by_turn.append(...)` called after every `client.messages.create()` call
- [ ] `record_agent_run()` called before every `return` in `run()`
- [ ] `record_agent_run` mocked in the agent's unit test so no real Sentry calls go out during tests
