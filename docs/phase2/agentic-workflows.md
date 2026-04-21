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

## Use cases to evaluate (not yet designed)

- [ ] Incremental feature development loop — Claude reads requirements, writes spec, waits for approval, writes failing tests, implements, verifies tests pass, opens PR
- [ ] Post-deploy validation — after every merge, Claude runs canaries and posts a health summary as a PR comment
