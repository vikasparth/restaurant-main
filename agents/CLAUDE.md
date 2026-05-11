# Agents Project Rules — Aap ki Rasoi

## Slice Rules (Agents)

The agents dependency map is at **`agents/specs/DEPENDENCY_MAP.md`**. Apply the generic slice rules from the root `CLAUDE.md` using this file as the layer's map.

**Every agent or extractor must have a spec in `agents/specs/` before any code is written.** The spec defines the signature, return shape, acceptance criteria, and TDD test plan. No implementation file may be created without a corresponding spec file that has been signed off. Retrospective specs are acceptable for code written before this rule was in place, but new work must always spec first.

## Agentic Observability — ALWAYS ACTIVE

- **Every agent `run()` must call `record_agent_run()` before every return path** — observability is not optional and must be wired at the time the agent is built, not retrofitted later.
- Token usage (`input_tokens`, `output_tokens`) is available free on every Anthropic API response — never discard it. Accumulate `usage_by_turn` during the loop and pass it to `record_agent_run()`.
- **No separate Anthropic calls for observability data** — read token counts from existing responses only.
- Confidence must be recorded numerically (high=3, medium=2, low=1) so trends can be charted over time in Sentry.

## Agent and Skill Design Principles

- **Skills are a packaging mechanism, not a reasoning mechanism.** Claude reasons equally well about which tool to call whether invoked via a skill or directly by an agent — MCP tools are visible in context either way.
- **A skill earns its place when a capability is reused across multiple agents, routable by name, or invocable by a human.** If none of these apply, putting the logic in the agent is simpler.
- **Write skills at intent level, not implementation level.** Describe what to accomplish and what output to produce — not which tool to call or in what order. A skill that names specific tools is tightly coupled and breaks silently when tools are renamed.
- **Hardcode tool names in a skill only when invoked directly by a human** with no agent layer. In that case determinism matters more than flexibility.
- **Agents own orchestration, routing, and one-off tasks. Skills own reusable, named, composable capabilities.**

## Agent Structure Rules

- Every agent lives in its own file: `agents/<name>_agent.py`.
- Every agent exposes a single `run() -> str` entry point that returns a YAML finding string.
- The agentic loop must be bounded by a max turns constant from `agents/config.py` — never an unbounded `while True`.
- Partial fallback YAML (`status: partial`) must be returned — never raise or return `None` when the turn budget is exhausted.

## Token Efficiency — ALWAYS ACTIVE

- **Never pass raw API responses into LLM context.** Tool functions must extract only the fields the LLM needs to reason about — not the full response object.
- **Apply time windows to all list queries.** Fetch only recent data (e.g. last 1 hour for live issues). Stale data is noise that wastes tokens.
- **Limit list results to 3–5 items maximum.** The agent investigates one issue at a time — the orchestrator decides which one. Fetching 25 issues to let Claude pick one is the wrong design.
- **Trim stack traces to the essential fields only:** exception type, exception message, culprit file, and top 1–2 frames. Breadcrumbs, request headers, and framework frames must be dropped before returning.
- **Target under 5k tokens per agent run** on Haiku. If a run exceeds this, review tool result payloads first.

## Observability Wiring Checklist

Before marking any agent task done, verify:
- [ ] `usage_by_turn` list initialised before the loop
- [ ] `usage_by_turn.append(...)` called after every `client.messages.create()` call
- [ ] `record_agent_run()` called before every `return` in `run()`
- [ ] `record_agent_run` mocked in the agent's unit test so no real Sentry calls go out during tests
