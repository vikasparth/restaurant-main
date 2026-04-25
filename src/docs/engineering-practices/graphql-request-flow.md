# GraphQL Request Flow

**Scope:** Frontend engineers working with the GraphQL gateway (`graphql-gateway/`).
**Last updated:** 2026-04-25

---

## Where the Code Runs

GraphQL involves two separate Apollo packages running in two separate places.

| Package | Where it runs | Installed in | Responsibility |
|---|---|---|---|
| `@apollo/client` | User's browser | `src/` | Sends queries, caches results, exposes `useQuery` / `useMutation` hooks |
| `@apollo/server` | Vercel Node.js server | `graphql-gateway/` | Receives queries, calls resolvers, filters response |

The user never sees Apollo Server. The frontend team never touches Apollo Client's network internals — they only write `gql` query strings and use hooks.

---

## HTTP Method — The Surprising Part

**React always sends HTTP POST to the gateway — for both queries and mutations.**

GraphQL uses POST for everything. The GET vs POST distinction only appears in the hop between the gateway and FastAPI, where your resolver decides.

| Hop | Method | Decided by |
|---|---|---|
| Browser → Gateway | Always `POST /graphql` | GraphQL spec |
| Gateway → FastAPI | `GET` for reads, `POST` for writes | Your resolver (`fetch` method option) |

---

## Example 1 — Query (menu fetch)

React asks for data. Full path from browser open to menu rendered on screen.

```mermaid
sequenceDiagram
    actor User
    participant B as Browser
    participant Vercel as Vercel (file server)
    participant APC as Apollo Client (browser)
    participant GW as GraphQL Gateway
    participant BE as FastAPI Backend
    participant DB as Supabase PostgreSQL

    User->>B: types your URL
    B->>Vercel: GET /
    Vercel-->>B: index.html + React JS bundle
    Note over B: React boots inside the browser tab — Vercel's job is done

    User->>B: clicks Menu link
    Note over B: React Router handles navigation — no server request
    B->>APC: MenuPage renders · useQuery(GET_MENU) fires
    Note over APC: cache miss — not fetched before
    APC->>GW: POST /graphql · { query: "{ menu { categories { name items { ... } } } }" }
    GW->>BE: GET /api/menu
    BE->>DB: SELECT * FROM menu_items WHERE is_available = true
    DB-->>BE: rows
    BE-->>GW: 200 { categories: [...] }
    GW->>GW: filter — keep only fields React asked for
    GW-->>APC: { data: { menu: { categories: [...] } } }
    APC->>APC: store result in cache
    APC-->>B: { data, loading: false }
    B-->>User: menu renders on screen
```

**Frontend code:**
```ts
const { data } = useQuery(GET_MENU);
// fires automatically when component renders
// result is cached — second render hits cache, not network
```

**Gateway resolver:**
```ts
Query: {
  menu: async () => {
    const response = await fetch(`${BACKEND_URL}/api/menu`); // GET by default
    return response.json();
  }
}
```

---

## Example 2 — Mutation (place order)

React sends data. Full path from page load to order confirmation on screen.

```mermaid
sequenceDiagram
    actor User
    participant B as Browser
    participant Vercel as Vercel (file server)
    participant APC as Apollo Client (browser)
    participant GW as GraphQL Gateway
    participant BE as FastAPI Backend
    participant DB as Supabase PostgreSQL
    participant Email as Resend
    participant WA as Twilio WhatsApp

    User->>B: opens order page
    B->>Vercel: GET /
    Vercel-->>B: index.html + React JS bundle
    Note over B: React boots inside the browser tab — Vercel's job is done
    Note over B: user fills in name, items, date, time

    User->>B: clicks Place Order
    B->>APC: useMutation fires · createOrder({ variables: { input: {...} } })
    Note over APC: mutations always skip cache — goes to network
    APC->>GW: POST /graphql · { mutation: "createOrder(input: { ... })" }
    GW->>BE: POST /api/orders · { customer, items, schedule }
    BE->>DB: validate items · fetch config · INSERT order
    DB-->>BE: order saved · reference_number generated
    BE->>Email: send confirmation email
    BE->>WA: send owner WhatsApp alert
    BE-->>GW: { reference_number, status, subtotal, total }
    GW-->>APC: { data: { createOrder: { reference_number, ... } } }
    APC-->>B: { data, loading: false }
    B-->>User: Order Confirmed screen · AKR-20260425-0042
```

**Frontend code:**
```ts
const [createOrder, { data, loading }] = useMutation(CREATE_ORDER);
// does NOT fire automatically — returns a function
// call createOrder({ variables: { input: {...} } }) on button click
```

**Gateway resolver:**
```ts
Mutation: {
  createOrder: async (_, { input }) => {
    const response = await fetch(`${BACKEND_URL}/api/orders`, {
      method: "POST",          // explicitly POST — write operation
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    return response.json();
  }
}
```

---

## Query vs Mutation — Key Differences

| | Query | Mutation |
|---|---|---|
| Purpose | Read data | Write data |
| Hook | `useQuery` | `useMutation` |
| When it fires | Automatically on render | Only when you call the returned function |
| Apollo cache | Result is cached | Always goes to network — never cached |
| Backend HTTP method | `GET` (by convention) | `POST` / `PUT` / `PATCH` (by convention) |
| GraphQL schema keyword | `type Query` | `type Mutation` |
| Input data | Arguments (optional) | `input` type (required for complex data) |

---

## Full Sequence — Order Placement

End-to-end view including caching behaviour and the browser/server boundary.

```mermaid
sequenceDiagram
    actor User
    participant Vercel as Vercel (file server)
    participant B as Browser · React
    participant APC as Apollo Client (browser)
    participant GW as Apollo Server · Gateway
    participant BE as FastAPI Backend · Render
    participant DB as Supabase PostgreSQL
    participant Email as Resend
    participant WA as Twilio WhatsApp

    Note over Vercel,B: Page load — happens once per visit
    User->>B: opens order page
    B->>Vercel: GET /
    Vercel-->>B: index.html + React JS bundle
    Note over B: React boots — Vercel's job is done
    Note over B: user fills form

    Note over B,WA: Order submission
    User->>B: clicks Place Order
    B->>APC: useMutation fires · createOrder({ variables })
    Note over APC: mutations skip cache — always hits network
    APC->>GW: POST /graphql · { mutation createOrder(input: {...}) }
    GW->>GW: parse · find Mutation.createOrder resolver
    GW->>BE: POST /api/orders · { customer, items, schedule }
    BE->>DB: validate items · fetch config · INSERT order
    DB-->>BE: saved · reference_number generated
    BE->>Email: send confirmation email
    BE->>WA: send owner WhatsApp alert
    BE-->>GW: { reference_number, status, subtotal, total }
    GW->>GW: filter to fields React asked for
    GW-->>APC: { data: { createOrder: { reference_number, ... } } }
    APC-->>B: { data, loading: false }
    B-->>User: Order Confirmed · AKR-20260425-0042
```

---

## What the Schema Does in This Flow

The `.graphql` schema file is the contract that makes Steps 2–3 safe:

- **React** can only ask for fields that exist in the schema — Apollo Client validates the query at build time via codegen
- **Gateway** rejects any query referencing a non-existent field before calling the resolver
- **CI** catches schema drift between the gateway schema and the backend `openapi.json`

See [graphql-guardrails.md](graphql-guardrails.md) for how the CI validation works.
