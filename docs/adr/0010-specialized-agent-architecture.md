# ADR-0010: Specialized Agent Architecture — Least Privilege + Orchestration Layer

**Status:** Accepted
**Date:** 2026-04-28
**Adds to:** `docs/engineering-practices/ai-agent-workflow.md` — Outer Loop section

## Context

The original `ai-agent-workflow.md` described the outer loop (operations monitoring) as a single agent that loads context incrementally — reading Sentry, source files, GitHub issues, and documentation in sequence within one session. The implementation constraint note explicitly stated: "Splitting into multiple specialised agents is not the solution to context bloat."

When designing the agentic troubleshooting workflow, a conflict emerged: a single agent that can read Sentry, GitHub, Render logs, and the codebase holds excessive privilege. In a production system, no single process should have read access to all external systems simultaneously. If the agent is compromised, misconfigured, or produces a hallucinated tool call, the blast radius is the union of all its access grants.

## Decision

Replace the single outer-loop agent with a fleet of specialized agents under an orchestration layer:

- **Sentry Agent** — Sentry API read-only; no access to codebase or GitHub
- **Render Logs Agent** — Render API read-only; no access to Sentry or GitHub
- **GitHub Agent** — GitHub API read-only by default; write access (issue comment) granted explicitly by the orchestrator only when confidence is high
- **Codebase Agent** — filesystem read-only, scoped to `src/`, `graphql-gateway/`, `backend/`, `docs/`; no external API access
- **Recommendation Agent** — no external access; synthesizes structured findings passed in from the orchestrator
- **Orchestrator** — invokes specialized agents, collects structured findings, routes to Recommendation Agent, delivers output

Each agent loads context incrementally within its own scope. The orchestrator decides which agents are needed based on the trigger type — not all agents run on every investigation.

Full design in `docs/engineering-practices/agent-architecture.md`.

## Alternatives Considered

**Single agent with incremental loading (prior approach):** Lower coordination overhead, simpler to build. Rejected because it cannot enforce least privilege — a single agent session with Sentry MCP + GitHub MCP + filesystem access holds all grants simultaneously regardless of what the current investigation step requires.

**Tool-scoped single agent (per-step tool restriction):** Restrict which tools the agent can call at each investigation step. Rejected because tool access in Claude Code is configured at the session level, not dynamically per step. Enforcing this at runtime is fragile.

## Consequences

- **Security:** each agent's access grant is bounded to its role; no single agent has the full picture
- **Least privilege enforced by design:** a Sentry Agent cannot accidentally (or adversarially) read source files; a Codebase Agent cannot post to GitHub
- **Coordination overhead:** the orchestrator adds a layer; handoffs between agents must be structured (not free-form prose) for the orchestrator to parse reliably
- **Testability:** each agent can be validated in isolation against its relevant test scenarios before wiring to the orchestrator
- **Cost:** more agent invocations per investigation; mitigated by the orchestrator only invoking agents whose signal is needed for the trigger type
