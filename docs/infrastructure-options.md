# Infrastructure Options — GraphQL Gateway & Chatbot Hosting

**Status:** Awaiting decision  
**Author:** AI Agent  
**Date:** 2026-04-27  
**Context:** The GraphQL gateway has never been deployed to production. The frontend on Vercel points to `localhost:4000`, causing a blank page in production. A chatbot is on the mid-term roadmap. This document evaluates deployment options before committing to an architecture.

---

## Constraints (Non-Negotiable)

- Infrastructure cost: **$0** — owner is only willing to pay for Claude API usage
- No DevOps expertise required — git-push-to-deploy or equivalent
- Must support **mid-term chatbot** (Claude API, streaming responses)
- Render free tier: **750 hours/month**, currently at 300 hours used

---

## Options Evaluated

### Option 1 — Vercel (Gateway) · Render (FastAPI) · Cloudflare Workers (Chatbot)

Deploy the GraphQL gateway as a Vercel serverless function. Keep FastAPI on Render unchanged. Add Cloudflare Workers only when the chatbot is needed.

| Dimension | Assessment |
|---|---|
| **Cost** | $0 — Vercel Hobby free, Render free, Cloudflare Workers free (100k req/day) |
| **Performance** | Gateway: ~100–300ms cold start on first request after idle; Render: 3s wake-up after 15min sleep |
| **Scalability** | Vercel auto-scales to thousands of concurrent requests; Render free tier is single instance, no auto-scaling |
| **Limitations** | Vercel Hobby: 10s function timeout — blocks long-running LLM calls; chatbot cannot go through gateway; WebSockets not supported on Vercel serverless |
| **Compliance** | Vercel: SOC 2 Type 2, GDPR compliant, US data centers; Cloudflare: global edge (data may transit non-US nodes) — review if customer PII in chat history is a concern |

**Best for:** Getting production working today with minimal change. Defer chatbot infrastructure until needed.

---

### Option 2 — Cloudflare Workers (Gateway + Chatbot) · Render (FastAPI)

Deploy both the GraphQL gateway and the future chatbot on Cloudflare Workers. Keep FastAPI on Render unchanged.

| Dimension | Assessment |
|---|---|
| **Cost** | $0 — Cloudflare Workers free (100k req/day), Render free |
| **Performance** | No cold starts — Workers are always warm globally; ~50ms response globally; Render still sleeps (3s wake-up) |
| **Scalability** | Workers auto-scale globally with no configuration; Render free is single instance |
| **Limitations** | Workers have 10ms CPU time limit per invocation — I/O bound operations (fetch calls to Render, Claude API) are fine; CPU-heavy processing is not; learning curve for Cloudflare ecosystem |
| **Compliance** | Cloudflare: global edge network — requests may be processed outside the US; review CCPA implications if chat history is stored; Cloudflare is SOC 2 Type 2 certified |

**Best for:** No cold starts today, single platform for all edge services, natural home for the chatbot when it comes.

---

### Option 3 — Vercel (Gateway) · Fly.io (FastAPI) · Cloudflare Workers (Chatbot)

Replace Render with Fly.io for the FastAPI backend. Fly.io free tier provides persistent VMs that never sleep.

| Dimension | Assessment |
|---|---|
| **Cost** | $0 — Vercel Hobby free, Fly.io free tier (3 shared VMs), Cloudflare Workers free |
| **Performance** | No sleep — always warm; no 3s cold start on first request; Vercel gateway still has ~100–300ms cold start |
| **Scalability** | Fly.io free: 3 VMs (256MB RAM each) — limited; paid tier scales well; Vercel auto-scales |
| **Limitations** | Fly.io requires a Dockerfile — more DevOps than Render's git-push; 256MB RAM per VM is tight for FastAPI under load; no git-connected auto-deploy on free tier |
| **Compliance** | Fly.io: SOC 2 Type 2, region-selectable (deploy in US-east or US-west); data residency is controllable — better than Cloudflare edge for strict US-only requirements |

**Best for:** Eliminating Render sleep latency proactively, if that becomes a real user complaint. Not justified today — no pain reported.

---

### Option 4 — Cloudflare Workers (Gateway + Chatbot) · Fly.io (FastAPI)

Full replacement: Cloudflare for all edge services, Fly.io for the persistent backend.

| Dimension | Assessment |
|---|---|
| **Cost** | $0 — all free tiers |
| **Performance** | Best of all options — no cold starts anywhere, global edge for gateway and chatbot, persistent backend |
| **Scalability** | Workers scale globally; Fly.io free tier is constrained (3 VMs, 256MB each) |
| **Limitations** | Highest operational complexity — two new platforms, Dockerfile required, Cloudflare and Fly.io both have learning curves; over-engineered for current traffic |
| **Compliance** | Fly.io gives US-only data residency for backend; Cloudflare edge processes requests globally — split compliance posture |

**Best for:** A production system with real traffic and performance requirements. Premature for current stage.

---

## Comparison Summary

| | Option 1 | Option 2 | Option 3 | Option 4 |
|---|---|---|---|---|
| **Cost** | $0 | $0 | $0 | $0 |
| **Gateway cold start** | Yes (~300ms) | No | Yes (~300ms) | No |
| **Backend cold start** | Yes (3s) | Yes (3s) | No | No |
| **Chatbot ready** | When needed | When needed | When needed | When needed |
| **WebSocket support** | No | Yes | No | Yes |
| **Setup complexity** | Low | Medium | High | High |
| **Platforms to learn** | 1 new | 1 new | 2 new | 2 new |
| **US data residency** | Partial | Partial | Yes | Partial |

---

## Compliance Notes (Training Data — Not Verified Against Current Certifications)

| Platform | SOC 2 | GDPR | US Data Residency |
|---|---|---|---|
| Vercel | Type 2 | Yes | Configurable |
| Render | Type 2 | Yes | US regions available |
| Cloudflare Workers | Type 2 | Yes | Global edge — not guaranteed US-only |
| Fly.io | Type 2 | Yes | Region-selectable — US controllable |

**Key compliance consideration for the chatbot:** if chat history containing customer names, phone numbers, or order details is stored or logged, CCPA applies (California customers). Cloudflare's global edge means that data may transit non-US nodes — verify with Cloudflare's Data Processing Addendum before storing PII in Workers KV or logs.

---

## Recommendation Trigger

Before deciding, confirm:
1. Is Render cold start latency a real user complaint, or theoretical?
2. Is the chatbot within 6 months, or further out?
3. Is US-only data residency a requirement, or a preference?

If cold start is not a problem and chatbot is 6+ months away → **Option 1** is sufficient today.  
If chatbot is within 6 months → **Option 2** avoids a second migration.
