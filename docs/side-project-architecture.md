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
    box Field Worker Device (thin client — no MCP installed)
        actor FW as Field Worker
    end
    box Microsoft Cloud
        participant Entra as Microsoft Entra ID
        participant Copilot as Copilot Studio (MCP Client)
        participant LLM as Azure OpenAI (GPT-4o)
    end
    box Company Backend (Azure / on-prem — MCP servers hosted here)
        participant KB as Knowledge Base MCP Server
        participant FS as Field Service MCP Server
        participant INV as Inventory MCP Server
    end

    Note over FW,Entra: ① Field Worker Auth (OAuth 2.0 — Authorization Code flow)
    FW->>Copilot: Opens Copilot app
    Copilot->>Entra: Redirect to login (client_id, scope, redirect_uri)
    Entra-->>FW: Login prompt (company SSO)
    FW->>Entra: Enters credentials
    Entra-->>Copilot: Authorization code
    Copilot->>Entra: Exchange code for tokens (client_secret)
    Entra-->>Copilot: Access token + ID token (JWT, expires 1h)
    Note over Copilot: Token identifies the worker — scopes control which tools they can call

    Note over Copilot,INV: ② Copilot → MCP Server Auth (OAuth 2.0 — Client Credentials flow, machine-to-machine)
    Copilot->>Entra: Request token for MCP servers (client_id + client_secret)
    Entra-->>Copilot: Service access token (scoped to MCP API)
    Note over Copilot,INV: Copilot uses this token for all MCP tool calls — workers never see it

    Note over FW,INV: ③ Tool Call Flow (HTTPS from Copilot Studio — not from field worker device)
    FW->>Copilot: "Camera not connecting after power cut — model DS-2CD2143G2"
    Copilot->>LLM: Forward query with system prompt + tool manifest
    LLM-->>Copilot: Call tool: search_troubleshooting_guide(model="DS-2CD2143G2", symptom="no connection after power")
    Copilot->>KB: HTTPS POST /tools/search_troubleshooting_guide [Bearer: service token]
    KB-->>Copilot: Returns top 3 diagnostic steps from KB article #4821

    LLM-->>Copilot: Call tool: get_service_history(device_serial="XYZ123")
    Copilot->>FS: HTTPS POST /tools/get_service_history [Bearer: service token]
    FS-->>Copilot: Last visit: 2024-11, replaced PoE switch — no open tickets

    Copilot->>LLM: KB result + service history → generate response
    LLM-->>Copilot: "Check PoE injector first — this model loses its IP lease after a hard reboot. Steps: 1) ... 2) ... 3) ..."
    Copilot-->>FW: Displays step-by-step diagnostic

    FW->>Copilot: "Step 2 didn't work — need to replace the PoE injector. What part?"
    Copilot->>LLM: Forward follow-up
    LLM-->>Copilot: Call tool: lookup_part_by_model(model="DS-2CD2143G2", component="PoE injector")
    Copilot->>INV: HTTPS POST /tools/lookup_part_by_model [Bearer: service token]
    INV-->>Copilot: Part #POE-48V-15W, in stock at Bristol depot (3 units)

    Copilot->>LLM: Part result → generate response
    LLM-->>Copilot: "Part #POE-48V-15W — 3 in stock at Bristol depot. Want me to raise a parts request?"
    Copilot-->>FW: Displays part info + action prompt

    FW->>Copilot: "Yes, raise the parts request and generate my job report"
    LLM-->>Copilot: Call tool: create_job_report(worker_id, job_summary, parts_used)
    Copilot->>FS: HTTPS POST /tools/create_job_report [Bearer: service token]
    FS-->>Copilot: Report #JR-20240502-089 created
    Copilot-->>FW: "Done — job report #JR-20240502-089 submitted, parts request raised."
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

## Key Design Decisions

| Decision | Rationale |
|---|---|
| MCP as the tool layer | Keeps Copilot decoupled from backend systems — each system gets its own server, independently deployable |
| One MCP server per domain | Matches team ownership (field ops, inventory, CRM are separate teams) |
| Copilot Studio as front-end | Meets Microsoft ecosystem requirement; handles auth, Teams integration, and mobile out of the box |
| Azure OpenAI (GPT-4o) as LLM | Required for Microsoft data residency and compliance guarantees in enterprise security/fire safety context |
| Stateless MCP tools | Tools are pure functions — session state lives in Copilot, not in the MCP layer |
