# Learning Log — Best Practices I Enforced

A record of cases where I pushed back on the AI's approach, forced better practices,
or created guardrails to prevent the same mistake from repeating.

---

## Hardcoding — Schema validator was hardcoded to Menu only

The schema validator script was initially written to check only `MenuItem` against
`openapi.json`. When asked about extending it, the response was to add another
hardcoded type.

I pushed back: the validator should work for any domain, not be rewritten every
time a new schema is added. This led to `validate-config.js` — a config-driven
approach where each new GraphQL type gets one entry in a mapping file, and the
validator loops over all of them automatically.

**Principle enforced:** Never hardcode domain-specific values into a script that
needs to work across all domains. Use configuration.

## Validators Must Fail Loudly and Cover All Cases

When the GraphQL schema validator was first wired into CI, it had two silent escape hatches: it only ran against `menu.graphql` by default, leaving every other schema file unchecked, and when it found an object type with no mapping in `validate-config.js` it emitted a warning rather than exiting with a non-zero code. Both meant the validator could pass CI while silently missing drift between the GraphQL schema and the backend OpenAPI contract — the exact problem it was built to catch.

The fix was two changes to `ci.yml`: loop over all `schemas/*.graphql` files so new features are never silently skipped, and make the unmapped-type check a hard failure (`process.exit(1)`) so a missing config entry blocks the PR rather than just printing a message.

**Guardrail created:** A validator that warns instead of failing, or that skips files by default, is not a validator — it is noise. Any new schema file must be covered automatically, and any coverage gap must be a CI failure.

---

## Comments — Code was labelled "self-documenting" to avoid writing WHY

Code was being written without comments, justified as "the code already says what
it does." I pushed back: code tells you WHAT it does, it cannot tell you WHY a
specific value was chosen, why a workaround exists, or what constraint a future
reader would miss.

**Guardrail created:** Added a Comments rule to `CLAUDE.md`:
- Comment the WHY, never the WHAT
- Only add a comment when a competent engineer reading cold would be confused without it
- Short inline format: `# reason why, not what`

---

## GraphQL Inspector — Accepted a suboptimal approach without verifying the alternative

The CI step for detecting breaking GraphQL schema changes was being implemented in
a way that would require manually updating the workflow every time a new schema file
was added. I questioned why the official `kamilkisiela/graphql-inspector@master`
GitHub Action could not be used instead.

This led to researching the official Action, which revealed a known limitation — it
does not support glob patterns (GitHub issue open since 2021, still unresolved).
The double-checkout pattern with the CLI was the correct approach, and was recorded
in ADR-0009.

**Principle enforced:** Always verify whether the "simpler" official tool has a
hidden limitation before accepting a workaround. Show your research.

---

## Challenge Skill — Recommendations were based on training data without verification

The `/challenge` skill was presenting alternatives and trade-offs based purely on
what the AI already knew from training, without checking whether that information
was still accurate or current.

I pushed back: AI training data has a cutoff. Tools get updated, issues get resolved,
better options emerge. Recommendations built on stale knowledge waste engineering time.

**Guardrail created:** Updated `/challenge` skill with a mandatory research step:
- Must use WebSearch/WebFetch before presenting any alternatives
- Must cite every source (URL, or explicitly label it "training data — not verified")
- If a source contradicts training data, trust the source

---

## Challenge Skill — Jumped to solutions without understanding the problem first

The `/challenge` skill would immediately restate the proposed approach and present
alternatives — without first checking whether the problem was correctly framed.

I pushed back: a better solution to the wrong problem is still the wrong solution.

**Guardrail created:** Added Step 0 to `/challenge` skill — a mandatory dialogue
phase that asks one investigating question at a time, working backwards from
outcomes, before any research or alternatives are presented.

---

## Architecture Diagrams — Only showed the happy path, not the full system

Diagrams were created showing the primary request/response flow but omitting side
effects (email, WhatsApp notifications), operational layers (monitoring, logging,
Sentry), and the auth model per route group.

I pushed back: a diagram that omits what the system actually does gives a false
picture. Engineers reading it would not know notifications are sent, monitoring is
active, or that different routes have different auth rules.

**Principle enforced:** Architecture and sequence diagrams must represent the full
system — all active layers, side effects, and auth — not just the data flow.

---

## Vercel — Misrepresented as having one role

Sequence diagrams included a note "Vercel's job is done" after serving the React
bundle, implying Vercel was no longer involved. In reality Vercel also hosts the
GraphQL Gateway (Apollo Server), which handles every GraphQL request after page load.

I caught this: Vercel has two distinct roles — CDN for static files, and Node.js
runtime for the gateway — and both must be visible in the diagram.

**Principle enforced:** When a platform hosts multiple things, represent each role
separately. Never collapse two responsibilities into one participant.

---

## Logging — No Consistent Strategy During Original Backend Implementation

When the backend was originally built, logging was added inconsistently and without a deliberate strategy. Routers got `print()` as a quick fix to ensure *something* appeared in Render logs on failure — and this was even codified in `backend/CLAUDE.md` as the correct pattern. Downstream services (email, WhatsApp, notifications) got a proper `logger`, but the core business services — `order_service`, `reservation_service`, `catering_service` — had no logging at all. There was no audit trail for when an order was created, a reservation confirmed, or a catering order submitted.

This gap only surfaced when the user prompted a review of the backend code during a later session. A logging strategy should be established before implementation begins, not retrofitted after the fact. The fix required updating six routers, adding success event logs to three core services, updating `backend/CLAUDE.md`, and creating `docs/engineering-practices/logging-strategy.md` to define layer rules, log structure, and PII guidelines for engineers and GenAI agents.

**Guardrail created:** Before implementing any backend feature, the logging strategy doc (`docs/engineering-practices/logging-strategy.md`) defines what must be logged and where. Every router must use `logger.exception()` for failures; every core business service must log a success event with reference number and structured `extra` fields when a record is created.

---

## Accessibility — ARIA Omitted from UI and Requirements

The frontend UI was being built without ARIA attributes. When the gap surfaced during Sentry breadcrumb debugging — where button identifiers were unreadable walls of Tailwind classes — the initial recommendation was to add `data-sentry-element` attributes to fix the monitoring problem. The user pushed back: coupling HTML to a specific monitoring tool is the wrong solution. The right solution is ARIA, a web standard that exists independently of any tool.

The deeper problem was that accessibility had no presence in the requirements document and no rules in `src/CLAUDE.md`. Without those guardrails, any page built by an engineer or AI agent would have the same gaps — inaccessible to screen readers, unselectable by Playwright, and producing unreadable Sentry breadcrumbs. Retrofitting ARIA across a full application is significantly more expensive than wiring it up correctly from the start.

**Guardrail created:** Added an Accessibility section to `src/CLAUDE.md` defining ARIA rules for every element type, and added ACC-01 through ACC-06 to `docs/requirements.md` as non-functional requirements. The rule: use proper ARIA (`htmlFor`/`id` pairs, `aria-label`, `aria-pressed`, `aria-hidden`) — never tool-specific attributes like `data-sentry-element` or `data-testid` as substitutes.

---

## Technical Debt — Defaulting to Legacy Standards Instead of Fixing Root Cause

When the GraphQL gateway returned 404 on Vercel, the AI diagnosed the problem as poor ESM support and switched the entire gateway from ESM to CommonJS to resolve the symptom. The actual root cause was a one-line tsconfig mismatch — `"type": "module"` in `package.json` paired with `"module": "CommonJS"` in `tsconfig.json`. The correct fix was setting `"module": "NodeNext"` and `"moduleResolution": "NodeNext"`, which is the proper pairing for ESM TypeScript and which Vercel supports correctly. The CommonJS workaround was never tested against the ESM path; it was reached for because it was familiar, not because ESM was genuinely unsupported.

Leaving CommonJS unchallenged would have compounded over time. The Node.js ecosystem is progressively dropping CommonJS — packages like `node-fetch` v3 are already ESM-only. CommonJS also lacks tree-shaking, inflating cold-start bundle sizes in serverless functions, and does not enforce strict module resolution semantics that catch import errors at compile time. The user caught this and pushed for an ESM fix, which worked on the first attempt once the tsconfig was corrected.

**Guardrail created:** Added to `CLAUDE.md` Engineering Principles: avoid technical debt — legacy fallbacks are a last resort. When a modern standard fails, diagnose and fix the root cause first. Only fall back to a legacy approach after exhausting all other paths, and document why when you do.

---

## Context Window Management — atomic tasks, indexed docs, and lean skills prevent token exhaustion

Running long sessions without clearing context causes two compounding problems. First, a bloated context window degrades Claude's reasoning quality — even after compaction, carrying excess history reduces the model's ability to think clearly on the current task. Second, it creates a real productivity risk: running to 100% token usage mid-work blocks progress until the quota resets, and emergency top-ups cost money.

The fix is architectural, not just behavioural. Execution plan tasks should be defined as atomic units of work — small enough that finishing one is a natural, safe point to clear the context window. Documentation should be indexed so Claude can be pointed to a specific section rather than parsing an entire file. Skill files must be kept as short as possible because their content persists in context for the entire session after invocation, even through compaction. The habit is: finish an atomic task, clear context, start fresh.

**Guardrail created:** Define execution plan tasks as atomic, index docs for targeted reference, keep skill files minimal, and clear the context window after each completed task set — never let a session run until token exhaustion.

---

## PII/PHI Scrubbing — Missing from Sentry Initialisation

When setting up Sentry across the frontend, backend, and GraphQL gateway, the `beforeSend` hook was not included as part of the initial Sentry configuration. The user had to prompt adding it after the fact. The hook scrubs known PII fields (`customer_name`, `customer_email`, `customer_phone`) from Sentry event payloads before they leave the application, ensuring customer data never reaches Sentry's servers.

This is not a nice-to-have — it is a baseline security and compliance requirement. Without it, any error that captures a request body (such as a failed reservation or order submission) could transmit customer personal data to a third-party logging service. This is a direct violation of GDPR and potentially other data protection regulations depending on jurisdiction. The risk is compounded by the fact that Sentry errors are often shared across a team and retained for months.

**Guardrail created:** Any `Sentry.init()` call across all layers (frontend, backend, gateway) must include a `beforeSend` hook that scrubs known PII/PHI fields before the event is sent. This requirement must be documented in CLAUDE.md so it is applied by default whenever Sentry is wired into a new service.

---

## Pre-Commit Hook Strategy — Wrong Tool for a Multi-Language Repo

When pre-commit hooks were first set up, Husky was chosen for the frontend and the `pre-commit` framework was chosen for the backend — two separate tools fighting over the same Git hook entry point. This worked initially, but was fragile from the start: every `npm install` on a fresh clone runs the `prepare` script, which re-installs Husky and sets `core.hooksPath`, silently overriding the `pre-commit` framework hooks and breaking backend checks without any visible error. The hooks appeared to be in place but were not firing for backend commits. Neither the engineers nor the AI caught this until it was explicitly questioned.

The correct choice from the beginning was the `pre-commit` framework for the entire repo. Despite its Python origins, `pre-commit` is a language-agnostic hook manager that handles frontend, backend, and gateway checks from a single config file. It does not get overwritten by `npm install`, and each hook only fires when files in its designated layer are staged. Using Husky for a multi-language repo is a misapplication of the tool — it is designed for Node.js projects and has no awareness of Python or gateway code. The migration to `pre-commit` for all three layers (backend, frontend, gateway) was recorded in `docs/developer-tooling.md`.

**Guardrail created:** In a multi-language monorepo, use the `pre-commit` framework as the single hook manager for all layers. Never use Husky alongside `pre-commit` — they conflict over `core.hooksPath` and `npm install` silently breaks the setup. New engineers must run `pre-commit install` after every fresh clone.

---

## Per-Project Env Ownership — Single Root `.env.example` Becomes a Liability

As a monorepo grows to include multiple sub-projects (frontend, backend, GraphQL gateway, agents), there is a temptation to maintain a single root `.env.example` as the one place to document all environment variables. This feels convenient early on, but the file grows verbose and loses structure quickly — variables for the agents team sit next to frontend `VITE_*` keys and backend database credentials with no clear ownership boundaries. When teams eventually split, or when a new engineer onboards to just one sub-project, they have no clean starting point and must mentally filter out everything irrelevant to their context.

DT-12 corrected this by giving each sub-project its own `.env.example`: `agents/.env.example`, `backend/.env.example`, `graphql-gateway/.env.example`, and a trimmed root `.env.example` covering only frontend vars. Each file is owned by the team that runs that sub-project — a change to backend secrets never touches the agents config, and vice versa. This is the same separation-of-concerns principle applied to configuration rather than code.

**Guardrail created:** Each sub-project owns its own `.env.example`; never consolidate environment variables into a root file as a project scales — separate teams need separate ownership boundaries.

---

## Observability Tooling — Defaulted to Custom Scripts When Sentry Was Already Running

When the user asked about tracking agent token usage and visualising it over time, the AI immediately proposed building custom tooling: a flat JSONL log file and a matplotlib script. Sentry was already wired into three layers of the project (frontend, backend, gateway) and has built-in support for exactly this use case — Performance transactions, custom measurements via `set_measurement()`, and dashboards. The proposal to build new infrastructure was never challenged against what was already in place.

Building custom observability scripts when a capable platform is already running adds unnecessary maintenance burden, splits the team's operational view across multiple tools, and signals a failure to think about the project holistically before proposing solutions. The correct move is to audit existing infrastructure first — new tooling is the right answer only when nothing covers the need.

**Principle enforced:** Before proposing new tooling, check what observability infrastructure is already running in the project. When Sentry is already wired in, it is almost always the right answer for token tracking, performance measurement, and visualisation — not a custom script.

## Agentic Observability — Token Usage and Confidence Must Be Logged

Every Anthropic SDK call returns token usage data on the response object at no extra cost — `response.usage.input_tokens` and `response.usage.output_tokens` are always present. The initial agent implementation discarded this data silently, meaning there was no visibility into how many tokens each agent consumed per run, which agents were expensive, or whether confidence levels were improving or degrading over time.

Without an observability layer, a feature or business owner has no way to correlate token spend with finding quality, identify agents that consistently exhaust their turn budget, or spot opportunities to tighten prompts and reduce cost. A low-confidence agent that also burns 3x the tokens of its peers is invisible without instrumentation — and so is a prompt regression that silently doubles token spend across all runs.

The fix was to accumulate `usage_by_turn` during the agentic loop from existing API responses (zero extra Anthropic calls), then call `record_agent_run()` once at the end of every `run()` to send a Sentry Performance transaction carrying token totals, turn count, and confidence as numeric data. This makes token budget planning, agent efficiency comparison, and confidence trend analysis available in a dashboard without any custom infrastructure.

**Guardrail created:** Every agent `run()` must instrument token usage and confidence via `record_agent_run()` — observability is not optional and must be wired at the time the agent is built, not added later.

## Agent Tool Results — Raw API Responses Must Never Enter LLM Context

When building the frontend Sentry agent, the tool functions were returning raw API responses directly into the LLM conversation — 25 full Sentry issue objects per call, and complete stack trace payloads including breadcrumbs, request headers, environment variables, and dozens of framework frames. The agent was also fetching issues with no time boundary, meaning month-old stale errors were being sent alongside recent ones. None of this extra data improved the quality of findings — it was pure token waste.

Left unchallenged, this pattern would compound with every agent added to the system. Each tool call that dumps a full API response into context multiplies token spend with no benefit. At 25k tokens per run on a Haiku model, costs would become prohibitive before the orchestration layer is even built, and the agentic loop would hit context limits mid-investigation on complex issues. The fix is to trim at the boundary — tool functions must extract only the fields the LLM needs to reason about, apply time windows to exclude stale data, and return the smallest payload that answers the question.

**Guardrail created:** Tool result functions must trim API responses before returning — extract only the fields the LLM needs, limit results to 3–5 items, and apply time windows where relevant. Raw API responses must never be passed directly into LLM context.

## Cross-Feature Imports — Shared Code Belongs in a Common Module

When building the Backend Sentry Extractor (D.2), the initial spec recommended importing shared helpers (`query_sentry_errors`, `get_stack_trace`, etc.) directly from `frontend_sentry_extractor.py`. The user pushed back: one feature module should never import from another. The right move was to refactor first — extract the shared functions into `agents/sentry_api.py` — then have both extractors import from there.

The problem with cross-feature imports is threefold. First, a developer working on the backend extractor must now read and understand frontend extractor code to know what they're depending on. Second, every future module that needs the same functions faces the same bad choice: import from an unrelated feature, or copy the code. Third, shared utilities buried inside a feature file are invisible to anyone scanning for common code — they won't find `sentry_api.py` if it doesn't exist yet.

**Guardrail created:** Before reusing code from one feature module in another, refactor the shared logic into a dedicated common file first. Cross-feature imports are not permitted.

## Pair Programming — Implementation Written Without Being Asked

When building `backend_sentry_extractor.py`, after writing the TDD tests, I proceeded to write the full implementation without waiting for the user to write it. The user had only asked me to write the spec and the tests — the implementation was never delegated. The pair programming rules in `CLAUDE.md` are explicit: guide the user to write the code one step at a time, explain the reasoning, and ask them to type it. Only boilerplate (imports, config, file scaffolding) can be written directly without prompting.

The problem is not just a process violation. The user is a new engineer learning Python by building this system. Every piece of implementation written on their behalf is a learning opportunity lost. Finishing the code for them feels helpful in the moment but undermines the entire purpose of the project. The rule exists to protect that learning goal — not as a style preference.

**Principle enforced:** Never write implementation code unless explicitly asked. Explain the next step, describe what the code needs to do, and ask the user to write it. Only boilerplate may be written directly.

## Skills as Packaging — Not Everything Belongs in the Agent

When explaining the difference between agents and skills, I framed the agent's advantage as Claude being better at picking the right tool than a skill with hardcoded tool names. I also claimed that open-ended and exploratory tasks are where agents shine over skills. The user pushed back correctly: an intent-based skill — one that describes what to accomplish rather than which tool to call — covers exactly the same open-ended cases. The reasoning capability is identical in both cases because Claude has MCP tools visible in context either way.

The real distinction is not about reasoning quality but about packaging. A skill earns its place when a capability needs to be reused across multiple agents, routable by name, or invocable directly by a human. Without this framing, a team would default to putting all logic inside agents — duplicating intent descriptions across agents, making capabilities invisible to orchestrators, and losing the ability to invoke them as slash commands. The correct mental model is: skills are a packaging mechanism for reusable capabilities; agents own routing and composition.

**Guardrail created:** When a capability needs to be shared across multiple agents or invoked by a human, define it as a named skill — do not embed it in the agent. Reserve agent-only logic for orchestration, routing, and one-off tasks unique to that agent.
