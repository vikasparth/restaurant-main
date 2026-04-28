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
