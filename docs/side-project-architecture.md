# Side Project — GenAI Field Agent Architecture

## Overview

Field workers and customers interact with a Microsoft Copilot Studio front-end.
Copilot orchestrates a set of MCP (Model Context Protocol) servers that expose domain-specific tools.
Each MCP server is a thin adapter over an existing backend system (CRM, knowledge base, field service, inventory).

---

## Use Cases

### Field Worker Use Cases

| # | Use Case | Description |
|---|---|---|
| FW-1 | AI Troubleshooting Copilot | Describe a symptom → agent walks through a model-specific diagnostic tree, pulling from device manuals and past tickets |
| FW-2 | Installation Guide Assistant | Voice or text query → step-by-step, model-specific wiring and config instructions from product documentation |
| FW-3 | Job Report Generator | Field worker dictates job summary → agent produces a structured completion report (work done, parts used, next service) |
| FW-4 | Parts & Inventory Lookup | Query by symptom or device model → returns part number and van/warehouse stock status |
| FW-5 | Escalation Decision Aid | Agent scores issue severity → recommends self-resolve, Tier-2 escalation, or return visit, and drafts the escalation note |

### Customer (End User) Use Cases

| # | Use Case | Description |
|---|---|---|
| CU-1 | Self-Help Troubleshooting Bot | Customer describes problem → guided resolution steps before raising a support ticket |
| CU-2 | Alarm Response Assistant | Alarm triggers → agent explains what it means, what to do now, and whether to call emergency services |
| CU-3 | Maintenance Scheduler | "Book a camera check" → agent checks contract, finds available slot, confirms appointment |
| CU-4 | Compliance & Audit Report Generator | Agent compiles service history, device test dates, and status into a formatted audit-ready report |

---

## Recommended Starting Points

| Priority | Use Case | Reason |
|---|---|---|
| 1 | FW-1 AI Troubleshooting Copilot | Fastest ROI — cuts callbacks and senior escalations |
| 2 | CU-1 Self-Help Bot | Deflects support tickets at scale |
| 3 | FW-3 Job Report Generator | Saves ~15 min per job; high adoption by field workers |

---

## Solution Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Microsoft Copilot Studio                    │
│           (Conversation UI — web, mobile, Teams)                │
└──────────────────────────────┬──────────────────────────────────┘
                               │  MCP Tool Calls
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
  │  Knowledge     │  │  Field Service │  │   Inventory    │
  │  Base MCP      │  │  MCP Server    │  │   MCP Server   │
  │  Server        │  │                │  │                │
  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
          │                   │                   │
          ▼                   ▼                   ▼
  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
  │  Device Manuals│  │  CRM / Work    │  │  ERP / Parts   │
  │  + KB Articles │  │  Orders / Jobs │  │  Stock System  │
  └────────────────┘  └────────────────┘  └────────────────┘
```

### MCP Servers and Their Tools

| MCP Server | Tools Exposed |
|---|---|
| **Knowledge Base MCP** | `search_troubleshooting_guide`, `get_device_manual`, `get_install_steps` |
| **Field Service MCP** | `get_work_order`, `create_job_report`, `get_service_history`, `draft_escalation` |
| **Inventory MCP** | `lookup_part_by_model`, `check_stock_level`, `find_nearest_warehouse` |
| **CRM MCP** | `get_customer_contract`, `get_site_devices`, `update_ticket_status` |
| **Compliance MCP** | `generate_audit_report`, `get_test_schedule`, `list_compliance_gaps` |

---

## Sequence Diagram — Field Worker Troubleshooting Flow

```mermaid
sequenceDiagram
    box Field Worker Device
        actor FW as Field Worker
        participant App as Copilot App (MCP Client)
        participant LocalMCP as Local MCP Server
    end
    box Microsoft Cloud
        participant Entra as Microsoft Entra ID
        participant LLM as Azure OpenAI (GPT-4o)
    end
    box Company Backend (Azure / on-prem)
        participant KB as Knowledge Base MCP Server
        participant FS as Field Service MCP Server
        participant INV as Inventory MCP Server
    end

    Note over FW,Entra: ① Field Worker Auth (OAuth 2.0 — Authorization Code flow)
    FW->>App: Opens Copilot app
    App->>Entra: Login redirect (client_id, scope, redirect_uri)
    Entra-->>FW: SSO login prompt
    FW->>Entra: Enters credentials
    Entra-->>App: Authorization code
    App->>Entra: Exchange code for tokens (client_secret)
    Entra-->>App: Access token + ID token (JWT, expires 1h)
    Note over App: Token identifies the worker — scopes control which tools they can call

    Note over App,INV: ② Machine-to-Machine Auth (Client Credentials flow — runs in background)
    App->>Entra: Request service token for remote MCP servers (client_id + client_secret)
    Entra-->>App: Service access token (scoped to MCP API)
    Note over App,INV: App uses this token for all remote MCP calls — worker never sees it

    Note over FW,INV: ③ Tool Call Flow — App routes each call to local or remote MCP based on tool type
    FW->>App: "Camera not connecting after power cut — model DS-2CD2143G2"
    App->>LLM: Forward query + full tool manifest (local + remote tools)
    LLM-->>App: Call tool: search_troubleshooting_guide(model="DS-2CD2143G2", symptom="no connection after power")

    Note over App,KB: KB search — try local cache first to handle poor signal on site
    alt Cache hit (offline KB on device)
        App->>LocalMCP: search_offline_kb(model, symptom)
        LocalMCP-->>App: KB article #4821 from local cache
    else Cache miss — fetch from remote KB
        App->>KB: HTTPS POST /tools/search_troubleshooting_guide [Bearer: service token]
        KB-->>App: KB article #4821 from live KB
        App->>LocalMCP: cache_article(#4821) — store locally for future offline use
    end

    LLM-->>App: Call tool: get_service_history(device_serial="XYZ123")
    Note over App,FS: Service history is live CRM data — always remote, never cached
    App->>FS: HTTPS POST /tools/get_service_history [Bearer: service token]
    FS-->>App: Last visit: 2024-11, replaced PoE switch — no open tickets

    App->>LLM: KB result + service history → generate response
    LLM-->>App: "Check PoE injector first — this model loses its IP lease after a hard reboot. Steps: 1) ... 2) ... 3) ..."
    App-->>FW: Displays step-by-step diagnostic

    FW->>App: "Let me take a photo of the fault"
    App->>LLM: Forward request
    LLM-->>App: Call tool: capture_photo()
    Note over App,LocalMCP: Device hardware — always local, no internet needed
    App->>LocalMCP: capture_photo()
    LocalMCP-->>App: photo_ref: /local/job_photos/img_001.jpg
    App->>LLM: Photo captured → acknowledge
    LLM-->>App: "Photo saved. Want me to attach it to the job report?"
    App-->>FW: Confirms photo captured

    FW->>App: "Yes, and what part do I need for the PoE injector?"
    LLM-->>App: Call tool: lookup_part_by_model(model="DS-2CD2143G2", component="PoE injector")
    App->>INV: HTTPS POST /tools/lookup_part_by_model [Bearer: service token]
    INV-->>App: Part #POE-48V-15W, in stock at Bristol depot (3 units)

    LLM-->>App: Call tool: create_job_report(worker_id, job_summary, photo_ref, parts_used)
    App->>FS: HTTPS POST /tools/create_job_report [Bearer: service token]
    FS-->>App: Report #JR-20240502-089 created with photo attached
    App-->>FW: "Done — report #JR-20240502-089 submitted with photo, parts request raised."
```

---

## Sequence Diagram — Customer Self-Help Flow

```mermaid
sequenceDiagram
    actor CX as Customer
    participant Copilot as Copilot Studio (Customer Portal)
    participant LLM as Azure OpenAI (GPT-4o)
    participant KB as Knowledge Base MCP Server
    participant CRM as CRM MCP Server

    CX->>Copilot: "My smoke alarm keeps beeping every 30 seconds"
    Copilot->>LLM: Forward query + customer context + tool manifest
    LLM-->>Copilot: Call tool: search_troubleshooting_guide(device_type="smoke_alarm", symptom="beeping every 30 seconds")
    Copilot->>KB: search_troubleshooting_guide(device_type, symptom)
    KB-->>Copilot: Match: low battery pattern — article #SH-102

    Copilot->>LLM: KB result → generate plain-English response
    LLM-->>Copilot: "A beep every 30 seconds usually means low battery. Here's how to replace it safely: ..."
    Copilot-->>CX: Displays self-fix steps

    CX->>CX: Tries the fix — still beeping

    CX->>Copilot: "I replaced it but it's still beeping"
    Copilot->>LLM: Follow-up + prior context
    LLM-->>Copilot: Call tool: get_site_devices(customer_id="C-4421")
    Copilot->>CRM: get_site_devices(customer_id)
    CRM-->>Copilot: Device: Hochiki ESP-120, installed 2019, last tested 2023

    LLM-->>Copilot: "Device is 5 years old and overdue a test — likely end of life. I can book a maintenance visit."
    Copilot-->>CX: Recommends booking + offers scheduling

    CX->>Copilot: "Yes please book it"
    LLM-->>Copilot: Call tool: book_maintenance_visit(customer_id, device_id, urgency="medium")
    Copilot->>CRM: book_maintenance_visit(...)
    CRM-->>Copilot: Appointment confirmed: 2026-05-06 10:00–12:00
    Copilot-->>CX: "Booked for 6 May, 10am–12pm. You'll get a confirmation email shortly."
```

---

---

## MCP Flow — Claude vs Copilot (Side-by-Side Reference)

Simple use case for both diagrams: **"Is the server healthy?"**
Maps to our `check_health_endpoint` MCP tool in the restaurant project.

---

### Claude — Without Agent (Skill invoked directly by human)

The LLM is Claude. The host is Claude Code. The skill names the tool explicitly
because there is no agent layer — Claude needs the hint to be deterministic.

```mermaid
sequenceDiagram
    actor User
    participant Host as Claude Code (MCP Host)
    participant LLM as Claude (LLM)
    participant Client as MCP Client
    participant Server as MCP Server

    User->>Host: /monitor-check
    Host->>Host: Loads SKILL.md into context
    Host->>LLM: User message + tool definitions + skill instructions
    Note over LLM: Reads skill: "Call check_health_endpoint()"
    LLM-->>Host: tool_use block — check_health_endpoint()
    Host->>Client: Execute tool call
    Client->>Server: POST /tools/check_health_endpoint
    Server-->>Client: { status: "healthy", latency_ms: 42 }
    Client-->>Host: Tool result
    Host->>LLM: Tool result — generate response
    LLM-->>Host: "Server is healthy. Latency 42ms, all metrics within threshold."
    Host-->>User: Displays response
```

---

### Claude — With Agent (Agent owns the loop)

The LLM still generates the tool_use block. The Agent manages the loop,
feeds results back, and decides when to stop — the LLM never talks to the MCP Server directly.

```mermaid
sequenceDiagram
    actor User
    participant Agent as Agent (loop + state)
    participant LLM as Claude (LLM)
    participant Client as MCP Client
    participant Server as MCP Server

    User->>Agent: "Is the server healthy?"
    Note over Agent: Registers tools from MCP Server at startup
    Agent->>LLM: Message + registered tool definitions
    Note over LLM: Reasons: "I should call check_health_endpoint"
    LLM-->>Agent: tool_use block — check_health_endpoint()
    Agent->>Client: Execute tool call
    Client->>Server: POST /tools/check_health_endpoint
    Server-->>Client: { status: "healthy", latency_ms: 42 }
    Client-->>Agent: Tool result
    Agent->>LLM: Tool result — continue?
    Note over LLM: No more tools needed — generate final response
    LLM-->>Agent: "Server is healthy. Latency 42ms."
    Agent-->>User: Final response
```

---

### Microsoft Copilot — Azure OpenAI (GPT) as LLM

Architecture is identical. GPT replaces Claude. Copilot Studio replaces Claude Code.
`function_call` replaces `tool_use`. The MCP Client still owns the transport in both.

```mermaid
sequenceDiagram
    actor User
    participant Host as Copilot Studio (MCP Host)
    participant LLM as Azure OpenAI / GPT (LLM)
    participant Client as MCP Client
    participant Server as MCP Server

    User->>Host: "Is the server healthy?"
    Host->>LLM: User message + tool definitions (from MCP Server manifest)
    Note over LLM: Reasons: "I should call check_health_endpoint"
    LLM-->>Host: function_call — check_health_endpoint()
    Host->>Client: Execute tool call
    Client->>Server: POST /tools/check_health_endpoint
    Server-->>Client: { status: "healthy", latency_ms: 42 }
    Client-->>Host: Tool result
    Host->>LLM: Tool result — generate response
    LLM-->>Host: "Server is healthy. Latency 42ms."
    Host-->>User: Displays response
```

---

### Key Differences at a Glance

| | Claude (no agent) | Claude (with agent) | Copilot / GPT |
|---|---|---|---|
| Host | Claude Code | Your Python Agent | Copilot Studio |
| LLM | Claude | Claude | Azure OpenAI / GPT |
| Tool call format | `tool_use` block | `tool_use` block | `function_call` JSON |
| Loop management | Claude Code (single turn) | Agent (multi-turn) | Copilot Studio |
| Tool name in skill? | Yes — determinism needed | No — agent owns routing | No — host owns routing |
| Transport owner | MCP Client | MCP Client | MCP Client |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| MCP as the tool layer | Keeps Copilot decoupled from backend systems — each system gets its own server, independently deployable |
| One MCP server per domain | Matches team ownership (field ops, inventory, CRM are separate teams) |
| Copilot Studio as front-end | Meets Microsoft ecosystem requirement; handles auth, Teams integration, and mobile out of the box |
| Azure OpenAI (GPT-4o) as LLM | Required for Microsoft data residency and compliance guarantees in enterprise security/fire safety context |
| Stateless MCP tools | Tools are pure functions — session state lives in Copilot, not in the MCP layer |
