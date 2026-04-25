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

## Step 1 — Credentials

The required credentials must be present in `backend/.env` before setup begins.

**If you are a human engineer:** request the values below from the team lead and populate `backend/.env` before proceeding.

**If you are an AI agent:** check that `backend/.env` exists and contains non-placeholder values for all required variables. If the file is missing or any required value is empty, stop and report which variables are missing — do not proceed with setup until they are provided.

Required variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase direct Postgres connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret for auth |
| `LOCATION_ID` | Restaurant location UUID |

See `backend/.env.example` for the full list of variables and their format.

---

## Step 2 — Backend Setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

**Configure environment variables:**

```bash
cp .env.example .env
```

Open `backend/.env` and fill in the values you received from the team lead. All other variables have working defaults for local development.

**Start the backend server:**

```bash
uvicorn main:app --reload
```

Backend runs on **http://localhost:8000**. Verify it is working: http://localhost:8000/health should return `{"status": "ok"}`.

---

## Step 3 — Frontend Setup

Open a new terminal tab (keep the backend running):

```bash
npm install
```

`npm install` also registers the Husky pre-commit hooks automatically — no extra step needed.

**Configure environment variables:**

```bash
cp .env.frontend.example .env.local
```

`VITE_SENTRY_DSN` can be left empty for local development.

**Start the frontend dev server:**

```bash
npm run dev
```

Frontend runs on **http://localhost:8080**. API calls to `/api/*` are automatically proxied to the backend at `http://localhost:8000` — no extra configuration needed.

---

## Step 4 — Pre-Commit Hooks

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

1. Backend: http://localhost:8000/health → should return `{"status": "ok"}`
2. Menu API: http://localhost:8000/api/menu → should return menu categories
3. Frontend: http://localhost:8080 → should load the restaurant website and display the menu

If the menu does not load, check that both servers are running and the `.env` database credentials are correct.
# test
