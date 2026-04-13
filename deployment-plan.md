# Deployment Plan — Aap ki Rasoi

## Overview

| Layer    | Platform | Source directory |
|----------|----------|-----------------|
| Backend  | Render   | `backend/`      |
| Frontend | Vercel   | `.` (repo root) |
| Database | Supabase | Already live    |

The frontend calls all APIs on relative `/api/...` paths. In development, Vite proxies them to `http://localhost:8000`. In production, a Vercel rewrite rule proxies them to the Render backend — no frontend code changes required.

---

## Pre-Deployment Checklist

Complete all items below before starting the deployment steps.

- [ ] **Move test deps to `requirements-dev.txt`** — remove `pytest`, `pytest-asyncio`, `httpx` from `requirements.txt`; confirm they exist in `requirements-dev.txt`
- [ ] **Add `backend/runtime.txt`** — single line: `python-3.12.10` so Render uses the correct Python version
- [ ] **Apply rate limits to public routes** — add `@limiter.limit()` to orders, reservations, and catering POST endpoints
- [ ] **Harden `/health` endpoint** — wrap `pool.acquire()` in try/except and return `503` on DB failure instead of unhandled 500

---

## Step 1 — Deploy Backend to Render

### 1.1 Create the Render service

1. Log in to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Set the following:

| Setting           | Value                                      |
|-------------------|--------------------------------------------|
| Root directory    | `backend`                                  |
| Runtime           | Python 3                                   |
| Build command     | `pip install -r requirements.txt`          |
| Start command     | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Python version    | `3.12.10`                                  |

### 1.2 Set environment variables on Render

Add every variable from `backend/.env` (except the blank RESEND line used for local dev):

| Variable              | Value                                        |
|-----------------------|----------------------------------------------|
| `DATABASE_URL`        | Your Supabase connection string              |
| `SUPABASE_URL`        | Your Supabase project URL                    |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT secret                     |
| `ENVIRONMENT`         | `production`                                 |
| `LOCATION_ID`         | `00000000-0000-0000-0000-000000000001`        |
| `ALLOWED_ORIGINS`     | _(fill in after Step 3 — Vercel URL)_        |
| `RESEND_API_KEY`      | Your Resend API key                          |
| `RESEND_FROM_EMAIL`   | `onboarding@resend.dev` (or verified domain) |
| `OWNER_EMAIL`         | Your email address                           |
| `TWILIO_ACCOUNT_SID`  | Your Twilio Account SID                      |
| `TWILIO_AUTH_TOKEN`   | Your Twilio Auth Token                       |
| `TWILIO_WHATSAPP_FROM`| `whatsapp:+14155238886`                      |
| `OWNER_WHATSAPP`      | `whatsapp:+<your-number>`                    |
| `INTERNAL_TOKEN`      | Your generated secret token                  |
| `NOTIFICATIONS_ENABLED` | `true` to enable email + WhatsApp, `false` to disable all notifications without code changes |

> **Feature flag:** Set `NOTIFICATIONS_ENABLED=false` on Render to silence all email and WhatsApp notifications instantly (e.g. during staging or if Resend/Twilio quotas are hit). Set to `true` to re-enable. Takes effect on next restart — no redeploy needed.

### 1.3 Verify backend is live

Once deployed, visit `https://<your-render-app>.onrender.com/` — you should see:
```json
{"message": "Aap ki Rasoi API is running"}
```

Also check `/health` returns `200 OK`.

**Note the Render URL — you will need it in Step 2.**

---

## Step 2 — Add vercel.json (API rewrite)

Create `vercel.json` at the **repo root** with the Render URL from Step 1.3:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://<your-render-app>.onrender.com/api/:path*"
    }
  ]
}
```

Commit and push this file before deploying to Vercel.

---

## Step 3 — Deploy Frontend to Vercel

### 3.1 Create the Vercel project

1. Log in to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Set the following:

| Setting          | Value         |
|------------------|---------------|
| Root directory   | `.` (default) |
| Framework preset | Vite          |
| Build command    | `npm run build` |
| Output directory | `dist`        |
| Node version     | `22` (LTS)    |

No environment variables needed — API calls go through the Vercel rewrite.

### 3.2 Verify frontend is live

Open the Vercel URL. The app should load and the menu should display (served from Supabase via the Render backend).

**Note the Vercel URL — you will need it in Step 4.**

---

## Step 4 — Wire CORS on Render

1. Go to Render → your web service → **Environment**
2. Update `ALLOWED_ORIGINS` to your Vercel URL:
   ```
   https://<your-vercel-app>.vercel.app
   ```
3. Click **Save Changes** — Render will redeploy automatically

---

## Step 5 — End-to-End Smoke Test

Run through this checklist on the live Vercel URL:

- [ ] Menu page loads (GET `/api/menu`)
- [ ] Delivery availability check works
- [ ] Place a delivery order → customer email received, owner WhatsApp received
- [ ] Make a reservation → confirmation shown
- [ ] Submit a catering enquiry → confirmation shown
- [ ] Visit `https://<render-url>/health` → `200 OK`

---

## Runtime Versions Reference

| Component | Version  |
|-----------|----------|
| Python    | 3.12.10  |
| Node      | 22 (LTS) |
| FastAPI   | 0.115.6  |
| Vite      | (see package.json) |

---

## Notes

- `backend/requirements-dev.txt` (black, flake8) is **not** installed on Render — only `requirements.txt` is used.
- The Twilio sandbox only delivers to verified numbers. For production WhatsApp notifications, upgrade to a Twilio paid number.
- `INTERNAL_TOKEN` secures the `/api/internal/send-reminders` endpoint called by pg_cron. Keep it secret.
- `RESEND_FROM_EMAIL` uses Resend's shared sandbox domain. To send from your own domain (e.g. `no-reply@aapkirasoi.com`), verify the domain in the Resend dashboard and update this variable.
