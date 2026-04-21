# Agentic Workflows
**Status:** Nice to have — evaluate use cases before building

## Before building anything here, answer these questions first

- Which problem is expensive enough in human time to justify the API cost per run?
- Where does human judgement add real value versus where is it just a rubber stamp?
- What is the failure mode if the agent gets it wrong — is it recoverable?

Only build an agent for a use case where the answer to all three is clear. Agents built without this clarity tend to be expensive, unreliable, and distrusted.

## How agents run

Claude Code CLI is designed for interactive use — it cannot run autonomously in GitHub Actions. Agentic workflows call the **Anthropic API directly** from CI. Cost is pay-per-token, charged per run, not covered by Claude Pro.

## One validated use case (design agreed, not yet built)

**Operational incident loop:**

```
Canary fails
→ GitHub issue opened (already built)
→ GitHub Actions triggered by issue creation (label: canary-failure)
→ Workflow calls Anthropic API with: issue content + metrics snapshot + runbook + relevant code files
→ Claude diagnoses root cause and generates a fix
→ GitHub Actions opens a PR with fix + diagnosis as PR description
→ Human reviews and approves PR
→ Merge → canaries rerun → issue auto-closes (already built)
```

Human stays in the loop at the approval gate. Claude handles diagnosis and fix generation only. Cost per run: fractions of a cent at Sonnet pricing — only fires on actual incidents, not on a schedule.

## Context window design — critical constraint

### Selective context loading (rule)

A single agent with access to all tools and skills will bloat context fast — Render logs + metrics + runbook + code files + skill instructions can reach 50-100k tokens for a complex incident. This makes responses slower, more expensive, and degrades Claude's attention on early details.

**The rule:** load only what the current step needs, nothing more.

```
Start lean — load only metrics snapshot
→ metrics point to server layer — load only Render logs + server runbook
→ diagnosis found — load only the specific code file implicated
→ generate fix for that file only
```

Context grows incrementally and only as far as the incident requires. Simple incidents stay cheap. Complex ones load more only if needed. This is already the pattern your monitor skills follow — `monitor-check` routes to one sub-skill, not all three simultaneously.

**Two agents are not the solution to context bloat.** Splitting into two agents adds coordination overhead and risks lossy handoff — Agent 2 only knows what Agent 1 chose to summarise. Disciplined tool use by one agent is the right answer.

### Information structure — what to pass to an agent (rule)

Before passing any data to an agent, ask: **what is the minimum structure needed for Claude to reason correctly?**

Passing raw responses bloats context with noise the agent cannot use. Every tool that feeds an agent must extract and return only the signal.

**Real example from this project:** `check_provider_status` fetched the full HTML status page from Twilio and Resend. The agent only needed one field — operational or degraded. The entire HTML body was wasted context.

**The design checklist for every tool that feeds an agent:**

| Question | Why it matters |
|---|---|
| What is the smallest unit of information Claude needs to make a decision? | Defines what to return |
| Is raw API/HTML response being passed directly? | If yes — extract and return only the relevant fields |
| Are there fields in the response Claude will never act on? | Strip them before returning |
| Is the response format consistent and predictable? | Unpredictable shapes force Claude to spend tokens parsing structure instead of reasoning |

**Applied to existing tools:**

| Tool | Current gap | What it should return |
|---|---|---|
| `check_provider_status` | Returns raw HTML status page | `{ provider, status: "operational/degraded", last_updated }` |
| `get_render_logs` | Returns raw log lines including noise | Pre-filtered lines containing `Exception`, `Error`, `Traceback`, 5xx — skip health check noise |
| `query_request_logs` | Good — already returns structured aggregates | No change needed |

Fixing tool output structure is higher leverage than adding more agents — a well-structured tool makes every skill that uses it cheaper and more accurate.

## Use cases to evaluate (not yet designed)

- [ ] Incremental feature development loop — Claude reads requirements, writes spec, waits for approval, writes failing tests, implements, verifies tests pass, opens PR
- [ ] Post-deploy validation — after every merge, Claude runs canaries and posts a health summary as a PR comment
