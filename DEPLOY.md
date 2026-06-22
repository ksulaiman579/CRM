# Deploying off your PC (Render + Vercel + Supabase)

DB is already on Supabase. This deploys the **backend** (FastAPI) to Render and
the **frontend** (Next.js) to Vercel, both auto-deploying from GitHub on push.

> Secrets (DB password, SECRET_KEY) are **never** committed — you paste them into
> the Render/Vercel dashboards. Use the values from `backend/.env` locally.

## Connection string to use for the deployed backend

Use the Supabase **Session pooler (port 5432)** URL — it's IPv4 and supports
migrations. Form (rewrite scheme to `postgresql+asyncpg`):

```
postgresql+asyncpg://postgres.sawpaohycijkeefsslib:<DB_PASSWORD>@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
```

## 1. Backend → Render

1. Render dashboard → **New → Blueprint** → connect `ksulaiman579/CRM`.
   It reads `render.yaml` and creates the `telecom-crm-api` web service.
2. Set the service's environment variables (Render → service → Environment):
   - `DATABASE_URL` = the session-pooler URL above (with your real password)
   - `SECRET_KEY` = the value from `backend/.env`
   - `CORS_ORIGINS` = `http://localhost:3000` for now (update in step 3)
   - (`DB_SSL` and `DB_DISABLE_STATEMENT_CACHE` are already set by the blueprint)
3. Deploy. The build runs `alembic upgrade head` then starts the API.
   Note the URL, e.g. `https://telecom-crm-api.onrender.com`.
   - Free tier sleeps when idle (first request after idle is slow).
   - **Keep it at 1 instance** — background jobs run in-process.

## 2. Frontend → Vercel

1. Vercel → **Add New → Project** → import `ksulaiman579/CRM`.
2. **Root Directory:** `frontend`.
3. Environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://telecom-crm-api.onrender.com/api/v1`
     (your Render URL + `/api/v1`)
4. Deploy. Note the URL, e.g. `https://telecom-crm.vercel.app`.

## 3. Wire CORS back

1. Render → `telecom-crm-api` → Environment → set
   `CORS_ORIGINS` = `https://telecom-crm.vercel.app` (your Vercel URL).
2. Save → Render redeploys. Done — the live frontend can now reach the API.

## After this

Every `git push` to `main` auto-redeploys both. We keep building features and
they ship to the live site automatically.

## Notes
- Demo login `admin / admin` — change before sharing publicly.
- SSE (live calls/notifications) works on Render; if a host buffers responses,
  streaming breaks — Render does not.
