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
