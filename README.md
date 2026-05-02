# Restaurant Main Project
Production-ready code for Aap ki Rasoi restaurant management website.

## Local Development Setup

This guide covers everything a new engineer (or AI agent) needs to run the project locally and develop features. Follow the steps in order.

---

## Prerequisites

Install these before starting:

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.11+
- [Git](https://git-scm.com/)

---

## Sub-project Overview

This repo contains four sub-projects, each owned by a separate team with its own dependencies and environment file:

| Sub-project | Language | Env file | Runs on |
|---|---|---|---|
| `src/` (Frontend) | TypeScript / React | `.env` (copied from `.env.example`) | http://localhost:5173 |
| `backend/` | Python / FastAPI | `backend/.env` (copied from `backend/.env.example`) | http://localhost:8000 |
| `graphql-gateway/` | TypeScript / Node.js | `graphql-gateway/.env` (copied from `graphql-gateway/.env.example`) | http://localhost:4000 |
| `agents/` | Python | `agents/.env` (copied from `agents/.env.example`) | CLI / scripts only |

---

## Step 1 — Credentials

Each sub-project needs its own `.env` file before setup begins. Copy each example file and fill in the required values:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp graphql-gateway/.env.example graphql-gateway/.env
cp agents/.env.example agents/.env
```

**If you are a human engineer:** request the values below from the team lead and populate each `.env` before proceeding.

**If you are an AI agent:** check that all four `.env` files exist and contain non-placeholder values for all required variables. If any file is missing or any required value is empty, stop and report which variables are missing — do not proceed until they are provided.

Required variables per sub-project:

| Sub-project | Required variables |
|---|---|
| Backend | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `LOCATION_ID` |
| Frontend | `VITE_SENTRY_DSN` (can be left empty for local dev) |
| Gateway | `BACKEND_URL` (default: `http://localhost:8000`) |
| Agents | `ANTHROPIC_API_KEY`, `SENTRY_AUTH_TOKEN`, `SENTRY_ORG_SLUG` |

See each sub-project's `.env.example` for the full variable list and where to get each value.

---

## Step 2 — Backend Setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Open `backend/.env` and fill in the values you received from the team lead. All other variables have working defaults for local development.

**Start the backend server:**

```bash
uvicorn main:app --reload
```

Backend runs on **http://localhost:8000**. Verify: http://localhost:8000/health should return `{"status": "ok"}`.

---

## Step 3 — Frontend Setup

Open a new terminal tab (keep the backend running):

```bash
npm install
```

`npm install` also registers the Husky pre-commit hooks automatically — no extra step needed.

`VITE_SENTRY_DSN` in `.env` can be left empty for local development.

**Start the frontend dev server:**

```bash
npm run dev
```

Frontend runs on **http://localhost:5173**. API calls to `/api/*` are automatically proxied to the backend at `http://localhost:8000` — no extra configuration needed.

---

## Step 4 — GraphQL Gateway Setup

Open a new terminal tab:

```bash
cd graphql-gateway
npm install
```

`BACKEND_URL` in `graphql-gateway/.env` defaults to `http://localhost:8000` — no change needed for local development.

**Start the gateway:**

```bash
npm start
```

Gateway runs on **http://localhost:4000**. The frontend proxies GraphQL requests through here to the backend.

---

## Step 5 — Agents Setup

The agents package is only needed if you are working on the agentic workflows (Phase 3). Skip this step otherwise.

```bash
cd agents
python -m venv .venv
source .venv/Scripts/activate       # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Fill in `agents/.env` with your `ANTHROPIC_API_KEY`, `SENTRY_AUTH_TOKEN`, and `SENTRY_ORG_SLUG`. `RENDER_API_KEY` and `GITHUB_TOKEN` are only needed for the Render Logs Agent (D.3) and GitHub Agent (D.4).

**Run the test suite:**

```bash
python -m pytest agents/tests/ -v
```

**Run an agent manually (smoke test):**

```bash
python -c "from agents.frontend_sentry_agent import run; print(run())"
```

---

## Step 6 — Pre-Commit Hooks

Pre-commit hooks automatically check your code for formatting and lint issues before every commit.

**Frontend hooks** are already registered by `npm install` in Step 3.

**Backend hooks** require one extra step. From the **project root**:

```bash
pip install pre-commit
pre-commit install
```

`pre-commit install` registers the hooks with your local git. Without this, backend hooks will not run on commit.

**What runs on every commit (staged files only):**

| Side | Checks |
|---|---|
| Frontend | ESLint + Prettier on `.ts` / `.tsx` files |
| Backend | Black format check + Flake8 lint on `backend/` files |

Tests are not run pre-commit — they run in CI on pull request.

---

## Verify Everything Works

1. Backend: http://localhost:8000/health → `{"status": "ok"}`
2. Menu API: http://localhost:8000/api/menu → returns menu categories
3. Frontend: http://localhost:5173 → loads the restaurant website and displays the menu
4. Gateway: http://localhost:4000 → GraphQL playground available

If the menu does not load, check that both servers are running and `backend/.env` database credentials are correct.
