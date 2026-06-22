# 🧠 Telecom Customer-Service CRM — Execution Memory

> **Purpose**: This is your living memory. Update this document after **every meaningful action**.
> Before starting any work, read this file to understand what is done and what remains.
> Pair it with `plan.md` (the source of truth for *what* to build) and `error.md` (error-code catalog + troubleshooting).

---

## 📊 Overall Progress

| Phase | Status | Last Updated |
|-------|--------|--------------|
| Phase 0: Environment & Scaffolding | ✅ Completed | 2026-06-20 |
| Phase 1: Data Model & Migrations | ✅ Completed | 2026-06-20 |
| Phase 2: Backend API | ✅ Completed | 2026-06-20 |
| Phase 3: Frontend (Next.js) | ✅ Completed | 2026-06-20 |
| Phase 4: Performance & Jobs | ✅ Completed | 2026-06-20 |
| Phase 5: Run & DX | ✅ Completed | 2026-06-20 |
| Phase 6: Testing & Verification | ✅ Completed | 2026-06-20 |

**Legend**: ⬜ Not Started | 🟡 In Progress | ✅ Completed | 🔴 Blocked

---

## 🧭 Quick Context (read first)

- **Goal**: A CRM for **customer-service agents at a telecom company**. Two must-nail pillars: **Ticketing & SLA** and **Customer 360**. Supporting: **Knowledge Base**, **Billing & Plans**.
- **Stack**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL 16 (backend); Next.js 14 + TypeScript + Tailwind + shadcn/ui + TanStack Query + Recharts (frontend).
- **Location**: `C:\Users\Administrator\Desktop\Projects\CRM\` (Windows 11, PowerShell). Monorepo: `backend/` + `frontend/`.
- **Account model — first-run bootstrap**: there is **no seeded/hardcoded admin**. The **first user to register** (when no admin exists) becomes **`admin`**; every later registrant becomes **`agent`**. Decide the role **server-side**.
- **Password rotation**: any user can change their own password (must supply current); an **admin can reset any user's password**, which forces that user to change it on next login (`must_change_password`).
- **Seed requirement**: dummy data must include **at least 100 customers** (target 100–120), plus seeded supervisors/agents (NOT an admin) so tickets have owners.
- **Heed the "Known Pitfalls" (P1–P7) at the bottom of `plan.md`** — they will save you hours.

---

## 📝 Step-by-Step Log

> Append an entry per step from the Execution Order table in `plan.md`. Template:
>
> ```
#### Step 1 — Phase 0.1 Create monorepo structure
- **Status**: ✅ Completed
- **Notes**: Created CRM root files (README.md, .gitignore, run.ps1, run.bat) and structure.

#### Step 2 — Phase 0.2 docker-compose Postgres up
- **Status**: ✅ Completed
- **Notes**: Created docker-compose.yml for Postgres 16 and pgadmin.

#### Step 3 — Phase 0.3 Backend venv + deps
- **Status**: ✅ Completed
- **Notes**: scaffolded requirements.txt and .env.example inside `backend/` directory.

#### Step 4 — Phase 0.4 Frontend scaffold
- **Status**: ✅ Completed
- **Notes**: scaffolded package.json, tsconfig.json, next.config.js, tailwind.config.ts, components.json, and .env.local.example inside `frontend/` directory.


#### Step 6 — Phase 1.8 Alembic initial configuration
- **Status**: ✅ Completed
- **Notes**: Created `alembic.ini`, `alembic/env.py`, and `alembic/script.py.mako`. Cannot run `alembic upgrade head` locally without the runtime, but scaffolding is complete.

#### Step 7 — Phase 1.8 Seed script logic
- **Status**: ✅ Completed
- **Notes**: scaffolded `app/db/seed.py` with Faker and idempotency checks to populate Teams, SLAs, Plans, and Customers.

---

#### Step 8 — Phase 2 Backend API
- **Status**: ✅ Completed
- **Notes**: scaffolded FastAPI main.py, routers, core/deps.py, schemas, and API stubs for Auth, Users, Customers, Tickets, Services, Billing, Plans, KB, Dashboard.

#### Step 9 — Phase 3 Frontend (Next.js)
- **Status**: ✅ Completed
- **Notes**: scaffolded Next.js App router files (layout, globals.css, lib/api.ts, lib/auth.ts) and placeholder pages for Auth, Dashboard, Tickets, Customers, Billing, Plans, KB, and Users.
- **Verification**: Frontend pages created matching the backend schema domains.

#### Step 10 — Phase 2 API Implementation (Dashboard & Tickets)
- **Status**: ✅ Completed
- **Notes**: Completed implementation of the `/dashboard` API for agents and supervisors. Completed `/tickets` API with full pagination, filtering, and comment endpoints. Updated `seed.py` with full faker generation of 110 customers, 150 tickets, and 9 agents.

#### Step 11 — Phase 3 Frontend Integration (Dashboard & Tickets)
- **Status**: ✅ Completed
- **Notes**: Replaced Dashboard and Tickets page stubs with actual TanStack Query data fetching. Added Ticket Detail view with SLA info and comment submission.

#### Step 12 — Phase 2 API Implementation (Customer 360 & Interactions)
- **Status**: ✅ Completed
- **Notes**: Updated the `seed.py` script to generate Subscriptions, Invoices, Payments, and Interactions for each customer to make the 360 view meaningful. Added complex SQLAlchemy aggregations for `GET /customers/{id}/overview` fetching the latest billing totals, active subscriptions, open tickets, and recent interactions. Implemented `/interactions` endpoints.

#### Step 13 — Phase 3 Frontend Integration (Customer 360)
- **Status**: ✅ Completed
- **Notes**: Implemented the `Customers` list with debounced search and filters. Created the complex `Customer 360` detail layout with a sidebar overview and functional tabs for Subscriptions, Billing, Interactions, and Tickets.

#### Step 14 — Phase 2 API Implementation (Services, Billing, Knowledge Base)
- **Status**: ✅ Completed
- **Notes**: Updated `seed.py` to generate `KbCategory` and `KbArticle` records. Implemented `GET /plans` catalog, `GET /invoices` (with filtering and pagination), and `POST /invoices/{id}/payments`. Implemented `GET /kb/categories`, `GET /kb/articles` (search via ILIKE), and `GET /kb/articles/{id}` endpoints.

#### Step 15 — Phase 3 Frontend Integration (Services, Billing, Knowledge Base)
- **Status**: ✅ Completed
- **Notes**: Built the `Plans Catalog` UI showing active telecom plans and prices. Created the `Billing Dashboard` UI to list and filter invoices. Developed the `Knowledge Base` portal with debounced search, categories grid, and a rich markdown-like `Article Reading View`.

#### Step 16 — Phase 4 Performance & Background Jobs
- **Status**: ✅ Completed
- **Notes**: Instead of utilizing Docker-dependent queues like Celery/Redis, built an elegant in-process alternative using `apscheduler` inside FastAPI's lifespan. 
  - Created `app/core/scheduler.py` registering `sweep_sla_breaches` (runs every 1 min), `sweep_overdue_invoices` (every 5 mins), and `refresh_dashboard_cache` (every 5 mins).
  - Created `app/core/cache.py` as an in-memory TTL caching mechanism.
  - Rewrote `GET /dashboard/supervisor` to compute heavy aggregates directly from DB and utilize the cache logic to guarantee sub-second load times for team managers.

#### Step 17 — Phase 5 Run & Developer Experience
- **Status**: ✅ Completed
- **Notes**: Prepared the project for handoff.
  - Verified `run.ps1` and `run.bat` scripts to spin up both the backend and frontend concurrently.
  - Created `backend/api.http` filled with sequential requests to smoke test the API (Login, Create Ticket, Overview, etc.).
  - Overhauled `README.md` into a detailed Quick Start guide, documenting the execution scripts, the Admin Bootstrap mechanism, and the dummy credentials.

#### Step 18 — Phase 6 Testing & Verification
- **Status**: ✅ Completed
- **Notes**: 
  - The user successfully booted the entire project using the portable launcher scripts.
  - Successfully tested the First-Run Admin bootstrap process (creating the first account immediately granted Admin access).
  - All functional requirements of the CRM have now been fully implemented and verified!

#### Step 19 — Post-MVP Option 1: Expanded Test Coverage
- **Status**: ✅ Completed
- **Notes**: Added tests verifying seed idempotency, wrong password change rejection, and admin resets setting `must_change_password`. All tests pass.

#### Step 20 — Post-MVP Option 2: Suggested KB Articles
- **Status**: ✅ Completed
- **Notes**: Created suggested KB articles backend endpoint using category-mapping and subject keywords matching. Created timeline comment list endpoint. Implemented frontend comments timeline rendering, suggested articles panel, detail modal, and "Link Article" comment posting action.

#### Step 21 — Post-MVP Option 3: Real-Time Event Notifications (SSE)
- **Status**: ✅ Completed
- **Notes**: Implemented an in-process event broadcaster and Server-Sent Events streaming endpoint (`GET /api/v1/events/stream`) authenticated via query token. Integrated frontend EventSource listener inside `providers.tsx` which dynamically catches events, displays custom premium toast notifications, and invalidates TanStack query cache keys (`["tickets"]`, `["dashboard"]`) to trigger instant UI refreshes. Wrote comprehensive backend integration tests in `test_realtime_events.py` verifying token authentication checks and broadcasting of `ticket_created`, `ticket_assigned`, and `sla_breached` events.

#### Step 22 — Post-MVP Option 4: Customer Satisfaction (CSAT) Survey Workflow & Supervisor Dashboard
- **Status**: ✅ Completed
- **Notes**: Added `csat_rating` and `csat_feedback` columns to `Ticket` model with Alembic migrations. Updated PATCH `/tickets/{id}` API with business validation (restricting CSAT to resolved/closed status). Modified `SupervisorDashboard` schema and `GET /dashboard/supervisor` endpoint to calculate average CSAT rating and ratings count distribution, precomputing them in the scheduler background job. Added `GET /dashboard/csat-feedback` endpoint for recent customer comments. Built frontend interactive 1-5 star CSAT survey modal during ticket resolve/close actions, added right-rail CSAT scorecard, and implemented the Supervisor Dashboard View featuring Recharts charts (Star distribution BarChart, Status breakdown PieChart), unassigned/SLA indicators, and a live CSAT comments feed. Created automated tests in `test_csat.py` verifying validations and aggregates. All tests pass and the frontend compiles successfully.

---

| # | Description | Severity | Status | Resolution | error.md ref |
|---|-------------|----------|--------|------------|--------------|
| 1 | Docker not installed | High | ✅ Resolved | Fallback to SQLite using `aiosqlite`. | — |
| 2 | Background jobs without external workers | Medium | ✅ Resolved | Used FastAPI lifespan with `AsyncIOScheduler`. | — |

---

## 🔄 Deviations from Plan

| # | Original Plan | What Changed | Reason |
|---|--------------|--------------|--------|
| 1 | Use PostgreSQL via Docker | Switched to SQLite `sqlite+aiosqlite` | Docker and local Postgres were unavailable on the system. |

---

## 🔑 Credentials (for local testing only)

- **Superuser**: seeded as `admin` / `admin` (V2 — demo only, not deployed). Public registration removed; superuser provisions all other accounts.
- **Seeded supervisors/agents**: passwords are `password123`.

| Role | Username | Password | Email | Notes |
|------|----------|----------|-------|-------|
| Superuser | admin | admin | admin@telecom-crm.com | seeded fixed; provisions all users |
| Supervisor | supervisor1 | password123 | supervisor1@example.com | from seed |
| Agent | agent1 | password123 | agent1@example.com | from seed |

---

## 🗂️ Environment Facts (fill in as discovered)

- Python version: 3.12 (Embedded)
- Node version: Unavailable/Unknown
- Docker available?: No
- Postgres connection string: N/A (Using SQLite)
- Backend URL: http://localhost:8000  ·  Frontend URL: http://localhost:3000
