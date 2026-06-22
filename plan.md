# 📋 Telecom Customer-Service CRM — Master Execution Plan

> **Agent**: You are the **executor** (Gemini). This document is your single source of truth.
> **Before every action**, re-read this plan and check `memory.md` for what has already been completed.
> **After every meaningful action**, update `memory.md` with what you did, what succeeded, what failed, and what's next.
> Use `memory.md` as your rubric — never repeat completed work, never skip incomplete work.

---

## 🎯 Project Overview

Build a **production-grade CRM for customer-service agents working at a telecom company**. This is an **agent workspace**, not a generic admin tool. Optimize every screen for the person who picks up a call/chat and has to resolve a customer's problem fast.

The four pillars of this product:

1. **Ticketing & SLA** — case management with queues, assignment, priority, escalation, and SLA countdown timers. This is the heart of an agent's day.
2. **Customer 360** — a single pane showing the customer's profile, subscriptions, devices/SIMs, billing status, and full interaction history.
3. **Knowledge Base** — searchable troubleshooting articles and call scripts agents reference while on a call, linkable to tickets.
4. **Billing & Plans** — supporting context so agents can answer "why is my bill high?" and "what plan am I on?" without leaving the app.

**Primary persona — the Customer-Service Agent:**
- Logs in, sees **My Queue** (assigned tickets, sorted by SLA breach risk).
- Receives a call → searches the customer → opens **Customer 360**.
- Reviews subscriptions/billing/past interactions → creates or updates a **ticket**.
- Consults the **Knowledge Base** for a fix → logs the interaction → resolves or escalates.

**Secondary personas:** Team Lead / Supervisor (queue oversight, reassignment, SLA reporting), Admin (users, plans, KB authoring, SLA policy config, password resets).

### Account model — first-run bootstrap (decided)

- **Self-registration is open**, but role assignment is automatic:
  - The **first person to register** (when no `admin` exists yet) becomes the **`admin`**.
  - **Every subsequent registrant** is created as an **`agent`**.
- Only an **admin** can later promote a user to `supervisor` or `admin`, or deactivate accounts.
- **Password rotation**: every user can change their own password (must supply the current one); an **admin can rotate/reset any user's password** (including their own) at any time.

### Tech Stack (decided)

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | **Python 3.12 + FastAPI** | Async REST API |
| ORM / Migrations | **SQLAlchemy 2.0 (async) + Alembic** | Typed models, versioned schema |
| Validation | **Pydantic v2** | Request/response schemas |
| Database | **PostgreSQL 16** | Run locally via Docker Compose |
| Auth | **JWT (access + refresh)** via `python-jose`, **bcrypt** hashing | Role-based access control |
| Frontend | **Next.js 14 (App Router) + React 18 + TypeScript** | |
| Styling | **Tailwind CSS + shadcn/ui** | Dark-mode-first design system |
| Data fetching | **TanStack Query (React Query)** | Server-state caching |
| Charts | **Recharts** | Dashboard visualizations |
| Seed data | **Faker** (Python script) | 100 customers + tickets + history |
| Local orchestration | **Docker Compose** (Postgres) + dev scripts | |

**Location:** `C:\Users\Administrator\Desktop\Projects\CRM\` (this directory — Windows 11, PowerShell).

**Constraints:**
- Keep the backend and frontend in **one monorepo** (`backend/` + `frontend/`).
- All secrets via `.env` files (never commit real secrets; commit `.env.example`).
- Multi-user from day one: stateless JWT API, per-request DB sessions, no global mutable state.
- The UI must be **demo-worthy** — clean, fast, keyboard-friendly for agents.

> **Note on prior build:** An earlier iteration used Python + NiceGUI + SQLite (single process). We are switching to FastAPI + Next.js + Postgres for a more conventional, scalable production CRM. The NiceGUI code is **not** reused. See the "Known Pitfalls" section at the end for lessons that still apply (auth/session, detached ORM objects, scheduler startup).

---

## 📁 Phase 0: Environment & Scaffolding

### 0.1 — Repository Structure

Create this structure inside `C:\Users\Administrator\Desktop\Projects\CRM\`:

```
CRM/
├── docker-compose.yml          # Postgres (+ optional pgadmin)
├── .gitignore
├── README.md
├── plan.md                     # (this file)
├── memory.md                   # (execution log)
├── error.md                    # (error-code catalog + troubleshooting)
│
├── run.ps1                     # one-shot dev launcher (PowerShell)
├── run.bat                     # one-shot dev launcher (cmd wrapper)
│
├── backend/
│   ├── .env.example
│   ├── pyproject.toml          # deps managed via uv or pip
│   ├── requirements.txt
│   ├── api.http                # REST Client smoke-test flows
│   ├── alembic.ini
│   ├── tests/                  # pytest: bootstrap + ticket lifecycle (required)
│   │   ├── conftest.py
│   │   ├── test_auth_bootstrap.py
│   │   └── test_ticket_lifecycle.py
│   ├── alembic/                # migrations
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app factory + router includes
│       ├── config.py           # Pydantic Settings (env-driven)
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py         # DeclarativeBase + naming conventions
│       │   ├── session.py      # async engine + get_db() dependency
│       │   └── seed.py         # Faker seed script (CLI entrypoint)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── security.py     # JWT create/verify, password hashing
│       │   ├── deps.py         # get_current_user, require_role deps
│       │   ├── errors.py       # AppError + exception handlers + error envelope
│       │   └── sla.py          # SLA timer + breach computation
│       ├── models/             # SQLAlchemy ORM models (one file per domain)
│       │   ├── __init__.py
│       │   ├── user.py         # User, Team, AuditLog
│       │   ├── customer.py     # Customer, Interaction
│       │   ├── service.py      # Subscription, Device/SIM
│       │   ├── billing.py      # Invoice, Payment, LineItem
│       │   ├── plan.py         # Plan, Addon, PlanFeature
│       │   ├── ticket.py       # Ticket, TicketComment, SlaPolicy
│       │   └── kb.py           # KbArticle, KbCategory
│       ├── schemas/            # Pydantic v2 request/response models (mirror models/)
│       │   └── ...
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py       # aggregates all v1 routers
│       │   └── v1/
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── customers.py
│       │       ├── tickets.py
│       │       ├── interactions.py
│       │       ├── billing.py
│       │       ├── plans.py
│       │       ├── kb.py
│       │       └── dashboard.py
│       └── services/           # business logic (keep routers thin)
│           ├── __init__.py
│           ├── ticket_service.py
│           ├── customer_service.py
│           └── dashboard_service.py
│
└── frontend/
    ├── .env.local.example
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── components.json         # shadcn/ui config
    └── src/
        ├── app/                # Next.js App Router
        │   ├── layout.tsx
        │   ├── globals.css
        │   ├── (auth)/login/page.tsx
        │   ├── (auth)/register/page.tsx
        │   ├── (auth)/change-password/page.tsx   # forced rotation
        │   └── (app)/          # authed shell (sidebar + header)
        │       ├── layout.tsx
        │       ├── page.tsx                 # Dashboard / My Queue
        │       ├── tickets/page.tsx
        │       ├── tickets/[id]/page.tsx
        │       ├── customers/page.tsx
        │       ├── customers/[id]/page.tsx  # Customer 360
        │       ├── billing/page.tsx
        │       ├── plans/page.tsx
        │       ├── kb/page.tsx
        │       ├── kb/[id]/page.tsx
        │       ├── users/page.tsx           # admin only
        │       └── profile/page.tsx
        ├── components/
        │   ├── ui/             # shadcn primitives
        │   ├── layout/         # Sidebar, Header, AppShell
        │   ├── tickets/        # TicketTable, TicketCard, SlaBadge
        │   ├── customer/       # Customer360 tabs
        │   ├── charts/         # Recharts wrappers
        │   └── common/         # StatCard, DataTable, SearchBar, StatusBadge
        ├── lib/
        │   ├── api.ts          # fetch wrapper w/ auth header + refresh
        │   ├── auth.ts         # token store, useAuth hook
        │   └── query.ts        # TanStack Query client
        ├── hooks/
        └── types/              # shared TS types mirroring API schemas
```

### 0.2 — Local Database (Docker Compose)

Create `docker-compose.yml` with a Postgres 16 service:

- DB name `telecrm`, user `telecrm`, password from `.env`.
- Expose port `5432`, persist with a named volume.
- (Optional) include `pgadmin` for inspection.

```powershell
docker compose up -d
```

> If Docker is unavailable on this machine, fall back to a local Postgres install and record the connection string in `memory.md`.

### 0.3 — Backend Dependencies

`backend/requirements.txt` (pin reasonably current versions):

```
fastapi>=0.115
uvicorn[standard]>=0.34
sqlalchemy[asyncio]>=2.0.40
asyncpg>=0.30
alembic>=1.14
pydantic>=2.10
pydantic-settings>=2.7
python-jose[cryptography]>=3.3
bcrypt>=4.2
python-multipart>=0.0.20
faker>=37.0
```

Install into a venv:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Update `memory.md`** after this step: record installed packages, Python version, and any errors.

### 0.4 — Frontend Scaffolding

```powershell
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --src-dir --eslint
npx shadcn@latest init
npm install @tanstack/react-query recharts lucide-react date-fns
```

Add the shadcn components you'll need: `button card table input select dialog badge tabs dropdown-menu avatar toast skeleton textarea`.

> **Update `memory.md`**: record Next.js version, installed shadcn components.

---

## 🗄️ Phase 1: Data Model & Migrations

Build SQLAlchemy 2.0 models (typed, `Mapped[...]` style) in `backend/app/models/`. Use a single Postgres database `telecrm` with proper foreign keys (no cross-DB "conceptual" references). Use Alembic for all schema changes.

> Use UTC `timestamptz` for all timestamps. Use Postgres `enum` or `CHECK`-constrained text for status fields. Add indexes on every foreign key and on common filter columns (`ticket.status`, `ticket.assigned_agent_id`, `customer.account_number`, etc.).

### 1.1 — Users, Teams, Audit (`models/user.py`)

```
users
├── id              BIGINT PK
├── username        TEXT UNIQUE NOT NULL
├── email           TEXT UNIQUE NOT NULL
├── password_hash   TEXT NOT NULL
├── full_name       TEXT NOT NULL
├── role            TEXT NOT NULL DEFAULT 'agent'   -- 'admin','supervisor','agent'
├── team_id         BIGINT FK -> teams.id NULL
├── is_active       BOOL DEFAULT TRUE
├── last_login      TIMESTAMPTZ
├── created_at      TIMESTAMPTZ DEFAULT now()
└── updated_at      TIMESTAMPTZ DEFAULT now()

teams
├── id              BIGINT PK
├── name            TEXT NOT NULL           -- e.g. 'Tier 1 Support', 'Billing Support'
└── description     TEXT

audit_log
├── id, user_id FK, action, target_type, target_id, details (JSONB), created_at
```

Roles & hierarchy: `admin > supervisor > agent`.

**No hardcoded admin.** The admin is created by **first-run bootstrap**: the first user to register becomes `admin`; all later registrants become `agent` (see §2.1). Do **not** seed an admin user (see §1.8) — leave the admin slot open for the first real registration.

Add a column `must_change_password BOOL DEFAULT FALSE` to `users` — set it `TRUE` when an admin resets someone's password, and prompt that user to rotate it on next login.

### 1.2 — Customers & Interactions (`models/customer.py`)

```
customers
├── id              BIGINT PK
├── account_number  TEXT UNIQUE NOT NULL    -- format "TC-XXXXXX"
├── first_name, last_name   TEXT NOT NULL
├── email           TEXT
├── phone_primary   TEXT NOT NULL
├── phone_secondary TEXT
├── national_id     TEXT UNIQUE
├── company_name    TEXT
├── customer_type   TEXT NOT NULL           -- 'residential','business','enterprise'
├── status          TEXT DEFAULT 'active'   -- 'active','suspended','terminated','pending'
├── segment         TEXT                    -- 'standard','premium','vip'  (drives priority)
├── address_line1, address_line2, city, state, zip_code, country
├── notes           TEXT
├── created_at, updated_at
   (no assigned_agent on customer — agents own tickets, not customers)

interactions                                -- every touchpoint, the spine of Customer 360
├── id              BIGINT PK
├── customer_id     BIGINT FK -> customers.id NOT NULL
├── ticket_id       BIGINT FK -> tickets.id NULL   -- interactions may belong to a ticket
├── agent_id        BIGINT FK -> users.id
├── channel         TEXT NOT NULL           -- 'call','email','chat','sms','in_person'
├── direction       TEXT                    -- 'inbound','outbound'
├── subject         TEXT NOT NULL
├── notes           TEXT
├── duration_sec    INT                     -- for calls
└── created_at      TIMESTAMPTZ DEFAULT now()
```

### 1.3 — Services: Subscriptions & Devices (`models/service.py`)

```
subscriptions
├── id, customer_id FK, plan_id FK
├── status          TEXT DEFAULT 'active'   -- 'active','paused','cancelled','expired'
├── start_date DATE NOT NULL, end_date DATE
├── auto_renew BOOL DEFAULT TRUE
├── monthly_charge  NUMERIC(10,2) NOT NULL  -- may differ from plan price (promos)
└── created_at, updated_at

devices                                     -- SIMs / routers / handsets on the account
├── id, customer_id FK, subscription_id FK NULL
├── device_type     TEXT                    -- 'sim','router','handset','set_top_box'
├── identifier      TEXT                    -- MSISDN / IMEI / serial
├── status          TEXT DEFAULT 'active'
└── activated_at    TIMESTAMPTZ
```

### 1.4 — Plans & Add-ons (`models/plan.py`)

```
plans
├── id, plan_code UNIQUE, name, description
├── plan_type       TEXT NOT NULL           -- 'mobile','fiber','dsl','satellite','bundle'
├── speed_mbps INT, data_cap_gb NUMERIC (NULL=unlimited)
├── voice_minutes INT (NULL=unlimited), sms_count INT (NULL=unlimited)
├── monthly_price NUMERIC(10,2) NOT NULL, setup_fee NUMERIC(10,2) DEFAULT 0
├── contract_months INT DEFAULT 12, is_active BOOL DEFAULT TRUE
└── created_at, updated_at

plan_features        -- id, plan_id FK, feature_name, feature_value, is_included
addons               -- id, name, description, price, addon_type, is_active
```

### 1.5 — Billing (`models/billing.py`)

```
invoices
├── id, invoice_number UNIQUE ("INV-YYYYMM-XXXX"), customer_id FK
├── billing_period_start DATE, billing_period_end DATE
├── subtotal, tax_amount, discount_amount, total_amount  NUMERIC(10,2)
├── status          TEXT DEFAULT 'pending'  -- 'pending','sent','paid','overdue','cancelled'
├── due_date DATE, paid_date DATE
└── created_at, updated_at

payments
├── id, payment_ref UNIQUE, invoice_id FK, customer_id FK
├── amount NUMERIC(10,2), payment_method TEXT, status TEXT DEFAULT 'completed'
├── transaction_ref TEXT, created_at, notes

line_items
├── id, invoice_id FK, description, quantity, unit_price, total, item_type
```

### 1.6 — Tickets & SLA (`models/ticket.py`) — CORE

```
sla_policies
├── id, name, priority TEXT          -- 'low','medium','high','critical'
├── first_response_mins INT NOT NULL -- target time to first response
├── resolution_mins     INT NOT NULL -- target time to resolution
└── is_active BOOL DEFAULT TRUE

tickets
├── id              BIGINT PK
├── ticket_number   TEXT UNIQUE NOT NULL    -- "TKT-YYYYMM-XXXXX"
├── customer_id     BIGINT FK -> customers.id NOT NULL
├── subject         TEXT NOT NULL
├── description     TEXT
├── category        TEXT NOT NULL           -- 'billing','network','technical','plan_change',
│                                           --   'complaint','provisioning','general'
├── priority        TEXT NOT NULL DEFAULT 'medium'  -- 'low','medium','high','critical'
├── status          TEXT NOT NULL DEFAULT 'open'    -- 'open','in_progress','pending_customer',
│                                                   --   'escalated','resolved','closed'
├── channel         TEXT                    -- origin: 'call','email','chat','web','sms'
├── assigned_agent_id BIGINT FK -> users.id NULL    -- NULL = in the unassigned queue
├── team_id         BIGINT FK -> teams.id NULL
├── sla_policy_id   BIGINT FK -> sla_policies.id NULL
├── first_response_at TIMESTAMPTZ           -- set on first agent reply
├── sla_response_due  TIMESTAMPTZ           -- created_at + policy.first_response_mins
├── sla_resolution_due TIMESTAMPTZ          -- created_at + policy.resolution_mins
├── sla_breached    BOOL DEFAULT FALSE      -- computed/maintained by SLA job
├── resolved_at, closed_at  TIMESTAMPTZ
├── created_by      BIGINT FK -> users.id
├── created_at, updated_at

ticket_comments                             -- the ticket timeline
├── id, ticket_id FK, author_id FK -> users.id
├── body            TEXT NOT NULL
├── is_internal     BOOL DEFAULT FALSE      -- internal note vs customer-facing reply
└── created_at      TIMESTAMPTZ DEFAULT now()
```

> **SLA logic** lives in `core/sla.py`: on ticket create, look up the active policy for the ticket's priority and stamp `sla_response_due` / `sla_resolution_due`. Expose helpers to compute remaining time and breach state for the UI. A background job (Phase 4) flags `sla_breached`.

### 1.7 — Knowledge Base (`models/kb.py`)

```
kb_categories     -- id, name, slug, description
kb_articles
├── id, title, slug UNIQUE, category_id FK
├── body            TEXT (markdown)
├── tags            TEXT[]                  -- Postgres array, for search/filter
├── status          TEXT DEFAULT 'published' -- 'draft','published','archived'
├── author_id FK -> users.id
├── view_count INT DEFAULT 0
└── created_at, updated_at
```

> Provide full-text search over `title`/`body`/`tags` (Postgres `tsvector` + GIN index, or `ILIKE` for v1). Agents must be able to find an article in <2 seconds.

### 1.8 — Migrations & Seed Data

1. Configure Alembic against the async engine; generate the initial migration covering all tables; run `alembic upgrade head`.
2. Build `db/seed.py` (idempotent, `Faker(seed=42)` for reproducibility) generating:
   - **Teams**: `Tier 1 Support`, `Tier 2 Technical`, `Billing Support`.
   - **Users**: **do NOT seed an admin** — the admin is created by first-run registration (§2.1). Seed only **2 supervisors + 7 agents** so tickets have owners; record their usernames/passwords in `memory.md`. (Bootstrap keys off "no admin exists", so seeded non-admin users do not block the first registrant from becoming admin.)
   - **SLA policies**: 4 (low/medium/high/critical) with sensible targets (e.g. critical = 15 min response / 4 h resolution; low = 8 h / 5 days).
   - **Plans**: 12 across mobile/fiber/dsl/bundle ($19.99–$299.99). **Add-ons**: 8.
   - **Customers**: **at least 100** (target 100–120) — 60% residential, 30% business, 10% enterprise; statuses ~75% active / ~10% suspended / ~10% pending / ~5% terminated; segment mix incl. some VIP/premium. This is a hard requirement: the dataset must contain **no fewer than 100 customers**.
   - Per customer: 1–2 subscriptions + devices, 3–12 months of invoices (70% paid / 20% pending / 10% overdue) with payments, and 1–5 interactions.
   - **Tickets**: ~150 spread across customers — realistic category/priority/status mix; ~30% unassigned (queue), some already breached, some resolved/closed; each with 1–6 comments forming a timeline.
   - **KB**: 6 categories, ~25 articles (billing disputes, no-signal troubleshooting, plan changes, SIM swap, router reset, roaming, etc.).
3. Provide a one-command seed: `python -m app.db.seed`.
   - **Idempotency guard (required):** on start, check whether data already exists (e.g. customer count > 0). If so, **skip** and print a notice — re-running must NOT duplicate the 100+ customers. Support `python -m app.db.seed --reset` to truncate the seeded tables (preserving any registered admin/users where sensible) and reseed cleanly. Use `Faker(seed=42)` so a reseed is reproducible.

> **Update `memory.md`** after seeding: record row counts per table and the seed command.

---

## 🔐 Phase 2: Backend API

Keep routers thin; put logic in `services/`. Every list endpoint must support **server-side pagination, filtering, and sorting** (`?page=&page_size=&sort=&...filters`). Return Pydantic response models. Protect everything except `/auth/login`, `/auth/register`, and `/health` with JWT.

### 2.0 — Error Handling & Error Codes (do this first)

Define a **single, consistent error contract** so the frontend and `error.md` stay in sync.

- **Error envelope** — every handled error returns this JSON shape with the right HTTP status:
  ```json
  { "error": { "code": "CRM-AUTH-002", "message": "Invalid username or password", "detail": null } }
  ```
- **Error code scheme**: `CRM-<DOMAIN>-<NNN>` where `<DOMAIN>` ∈ `AUTH, USER, CUST, TKT, SLA, BILL, PLAN, KB, DASH, SYS`. Keep codes stable once assigned.
- Implement an `AppError(code, message, http_status, detail=None)` exception in `core/errors.py` and a FastAPI **exception handler** that renders the envelope. Also handle `RequestValidationError` (→ `CRM-SYS-422`) and uncaught exceptions (→ `CRM-SYS-500`, log the traceback, never leak internals).
- **Every time you introduce a new code, add a row to `error.md`** (code · meaning · cause · fix). The seed list of codes is already in `error.md`.
- Frontend `lib/api.ts` reads `error.code`/`error.message` and surfaces a friendly toast; for unexpected codes it shows the message and logs the code to the console.

### 2.1 — Auth & Security (`core/security.py`, `api/v1/auth.py`)

- `hash_password` / `verify_password` using **bcrypt** directly (do **not** use passlib — see Known Pitfalls).
- JWT: short-lived **access token** (e.g. 30 min) + longer **refresh token** (e.g. 8 h). Endpoints:
  - `POST /auth/register` → self-registration with **first-run bootstrap**:
    - In a transaction, check whether any user with role `admin` exists.
    - **No admin exists** → create this user as **`admin`** (this is the first-run owner).
    - **An admin already exists** → create this user as **`agent`** (ignore any client-supplied role).
    - Use a uniqueness/locking strategy (e.g. `SELECT … FOR UPDATE` or a unique partial index on `role='admin'` won't fit since multiple admins are allowed later — instead guard with a transaction + count, and rely on the `username`/`email` unique constraints) so two simultaneous first registrations can't both become admin.
    - Returns `{access, refresh, user}` (auto-login after registration); writes an audit-log entry noting the bootstrapped role.
  - `POST /auth/login` → `{access, refresh, user}` (updates `last_login`, writes audit log; include `must_change_password` in the user payload so the UI can force a rotation).
  - `POST /auth/refresh` → new access token.
  - `POST /auth/logout` → invalidate refresh (token blacklist table or short TTL).
  - `GET /auth/me` → current user.
  - `POST /auth/change-password` → **self password rotation**: body `{current_password, new_password}`; verify the current password, enforce a strength rule (min length etc.), re-hash, clear `must_change_password`, write audit log. Available to **every** authenticated user (including admin rotating their own password).
- `core/deps.py`: `get_current_user` (decode JWT, load user) and `require_role(*roles)` dependency factory.

> **Return plain Pydantic/dict from the user dependency**, not a live ORM object held across the request, to avoid `DetachedInstanceError` (see Known Pitfalls).

### 2.2 — Tickets API (`api/v1/tickets.py`) — CORE

- `GET /tickets` — paginated, filter by `status`, `priority`, `category`, `assigned_agent_id`, `team_id`, `customer_id`, `sla_breached`, free-text `q`; sort by SLA due / created / priority. Support a **`scope=my|queue|team|all`** shortcut (`my` = assigned to me, `queue` = unassigned).
- `GET /tickets/{id}` — full ticket + customer summary + comments timeline + linked interactions + SLA status.
- `POST /tickets` — create (auto ticket_number, auto SLA stamping, optional auto-assign).
- `PATCH /tickets/{id}` — update status/priority/category/assignment; set `first_response_at` on first agent reply; set `resolved_at`/`closed_at` on status change; write audit log.
- `POST /tickets/{id}/assign` — assign/claim (`{agent_id}` or self-claim).
- `POST /tickets/{id}/escalate` — bump priority/status to escalated, optionally reassign team.
- `POST /tickets/{id}/comments` — add comment/reply (`is_internal` flag).

### 2.3 — Customers API (`api/v1/customers.py`) — Customer 360

- `GET /customers` — paginated search (name, account #, phone, email), filter by status/type/segment.
- `GET /customers/{id}` — profile.
- `GET /customers/{id}/overview` — **aggregated 360 payload**: profile + active subscriptions + devices + billing summary (balance, last invoice, overdue count) + open ticket count + recent interactions. (Power the Customer 360 page with one call.)
- `GET /customers/{id}/subscriptions`, `/billing`, `/interactions`, `/tickets` — tab data, each paginated.
- `POST /customers`, `PATCH /customers/{id}` — create/update.

### 2.4 — Interactions API (`api/v1/interactions.py`)

- `POST /interactions` — log a call/chat/email against a customer (and optionally a ticket).
- `GET /interactions?customer_id=&ticket_id=` — paginated history.

### 2.5 — Billing & Plans APIs

- `billing.py`: `GET /invoices` (filter status/customer/date range), `GET /invoices/{id}` (with line items), `POST /invoices`, `POST /invoices/{id}/payments` (record payment, flip status to paid), billing summary endpoint.
- `plans.py`: `GET /plans` (+ subscriber counts), `GET /plans/{id}`, `POST`/`PATCH` (admin/supervisor), `GET /addons`.

### 2.6 — Knowledge Base API (`api/v1/kb.py`)

- `GET /kb/articles?q=&category=&tag=` — full-text search, paginated.
- `GET /kb/articles/{id}` — article (increment `view_count`).
- `POST`/`PATCH`/`DELETE` — author/manage (admin/supervisor); `GET /kb/categories`.

### 2.7 — Dashboard API (`api/v1/dashboard.py`)

- `GET /dashboard/agent` — for the logged-in agent: my open tickets, tickets due/breaching soon, resolved today, avg handle time.
- `GET /dashboard/supervisor` — team queue depth, unassigned count, SLA breach rate, tickets by status/category, agent workload, 12-month resolution trend, CSAT placeholder.
- Cache expensive aggregates (Phase 4).

### 2.8 — Users & Audit API (`api/v1/users.py`)

- **Admin only — manage other users:**
  - `GET /users` (list, filter by role/team/status), `POST /users` (admin-created account with an explicit role), `PATCH /users/{id}` (edit name/email/role/team, activate/deactivate via `is_active` soft delete).
  - `POST /users/{id}/reset-password` → **admin password rotation for any user**: sets a new password (admin-supplied or a generated temporary one returned once in the response), sets `must_change_password=TRUE`, writes audit log. The admin can target their own id too.
  - `POST /users/{id}/promote` (optional convenience) → change role to `supervisor`/`admin`.
- Supervisors: read-only user/team visibility (no role changes, no password resets) — keep write operations admin-gated.
- Agents: only `GET /auth/me`, update own profile, and `POST /auth/change-password`.
- `GET /audit-log` (admin) with filters — must capture logins, role bootstraps, password resets/rotations, and ticket actions.

---

## 🎨 Phase 3: Frontend (Next.js)

Dark-mode-first, agent-optimized. Use shadcn/ui + Tailwind. All data via TanStack Query against the API in `lib/api.ts` (attaches access token, auto-refreshes on 401).

### 3.1 — Design System & Theme (`globals.css`, `tailwind.config.ts`)

Define CSS variables / Tailwind theme tokens:

```
primary       #6366F1 (indigo)   secondary #06B6D4 (cyan)
success       #10B981            warning   #F59E0B    danger #EF4444
bg            #0F172A (slate-900) surface  #1E293B (slate-800)
hover         #334155            border    #334155
text          #F8FAFC            muted     #94A3B8
```

- Font **Inter** (or Plus Jakarta Sans). Radius 12px cards / 8px inputs. 0.2s transitions.
- **SLA color semantics** (reuse everywhere): green = on track, amber = due soon (<25% time left), red = breached.
- Status/priority badges with consistent colors. Category icons (lucide-react).

### 3.2 — App Shell & Auth (`app/(app)/layout.tsx`, `lib/auth.ts`)

- **Login** (`/login`): centered card on gradient, username/password, error states, loading button, plus a **"Create account"** link to `/register`.
- **Register** (`/register`): username, email, full name, password (+ confirm) with strength hints. On submit it calls `POST /auth/register` and auto-logs-in. Surface the bootstrap outcome to the user — if they became the **admin** (first run), show a brief "You're the administrator" confirmation; otherwise they land as an agent. The role is decided **server-side** — never let the client pick it.
- **Forced password rotation**: if the logged-in user has `must_change_password=true` (e.g. after an admin reset), redirect them to a change-password screen before they can use the app.
- **Profile → Security**: every user has a "Change password" form (current + new). Admins additionally get a "Reset password" action on each user row in the Users page.
- Store tokens (access in memory + refresh; persist refresh in an httpOnly-style cookie if doing SSR, else `localStorage` for v1 — document the choice). `useAuth()` hook; redirect unauthenticated users to `/login`; route guards by role.
- **App shell**: collapsible left sidebar (Dashboard, **My Queue/Tickets**, Customers, Billing, Plans, Knowledge Base, Users [admin]), top header with **global customer search**, notifications bell, user menu (profile, logout).

### 3.3 — Dashboard / My Queue (`app/(app)/page.tsx`) — agent landing

- **KPI cards**: My open tickets · Due soon (amber) · Breached (red) · Resolved today.
- **My Queue table**: my assigned tickets sorted by SLA due, with live SLA countdown badges, priority, customer, category, status — row click → ticket detail.
- **Unassigned Queue** panel: claimable tickets (one-click "Claim").
- Supervisors additionally see team widgets (queue depth, breach rate, workload bar chart, 12-month resolution trend line — Recharts).

### 3.4 — Tickets (`tickets/page.tsx`, `tickets/[id]/page.tsx`) — CORE

- **List**: scope tabs (My / Queue / Team / All), rich filters (status, priority, category, agent, breached), search, server-side pagination, SLA badges.
- **Detail** (the agent's main workspace):
  - Header: ticket #, subject, status/priority/category controls, **SLA countdown**, assign/claim, escalate.
  - Left/main: **comment timeline** (customer replies vs internal notes), composer with internal-note toggle.
  - Right rail: **mini Customer 360** (name, account #, segment, active plan, balance, open tickets) with a link to full profile; linked interactions; "Log interaction" button.
  - "Suggested articles" from KB based on category/keywords (nice-to-have).
- **New ticket** dialog: pick customer (search), subject, category, priority, channel, description.

### 3.5 — Customer 360 (`customers/page.tsx`, `customers/[id]/page.tsx`)

- **List**: search (name/account/phone/email), filters (status/type/segment), paginated table, "Add Customer".
- **Detail = Customer 360** powered by `/customers/{id}/overview`, with tabs:
  - **Overview**: contact + address, segment, account status, billing summary (balance, last/overdue invoices), quick actions (New Ticket, Log Interaction).
  - **Subscriptions**: active plans, add-ons, devices/SIMs.
  - **Billing**: invoice history + payment history + record-payment action.
  - **Interactions**: full timeline (calls/chats/emails) + add new.
  - **Tickets**: all tickets for this customer with status/SLA.

### 3.6 — Billing (`billing/page.tsx`)

- Summary cards (billed this month / collected / outstanding / overdue). Invoice table (filter status/date/customer). Create-invoice dialog (customer + line items + discount). Record-payment flow. Invoice detail with line-item breakdown.

### 3.7 — Plans (`plans/page.tsx`)

- Plan cards in a grid (name, speed, data cap, price, features, subscriber count), color-coded by type (mobile=cyan, fiber=indigo, dsl=amber, bundle=emerald). Add/Edit dialog (admin/supervisor). Add-ons section.

### 3.8 — Knowledge Base (`kb/page.tsx`, `kb/[id]/page.tsx`)

- Prominent **search bar** + category/tag filters; article cards with category + view count. Article page renders markdown, shows related articles, "link to current ticket" affordance. Authoring (create/edit, draft/publish) for admin/supervisor.

### 3.9 — Users & Profile

- **Users** (admin: full control; supervisor: read-only view): table with role/team/status/last-login badges. **Admin-only** actions: create/edit drawer, deactivate, **reset password** (rotates the user's password and flags `must_change_password`), promote role, audit-log viewer (searchable/filterable).
- **Profile**: view/edit own name/email, **change password** (requires current password — self password rotation), own recent login history. The forced-rotation screen reuses this form.

---

## ⚡ Phase 4: Performance, Multi-User & Background Jobs

### 4.1 — Multi-User & Concurrency
- Stateless JWT API → horizontally scalable; no server-side per-user mutable globals.
- **Server-side pagination** on every list endpoint; never ship full tables to the client.
- Async SQLAlchemy with a **per-request session** via FastAPI dependency (`get_db`), always closed after the request.
- Connection pooling on the async engine (`pool_size`, `max_overflow`); sensible statement timeout.
- Indexes on all FKs + hot filter columns (see Phase 1).

### 4.2 — Background Jobs
Run a scheduler (APScheduler `AsyncIOScheduler` started inside FastAPI's **lifespan** handler — not at import time; see Known Pitfalls) for:
- **SLA sweep** (every 1–2 min): flag `sla_breached`, surface breaching-soon tickets.
- **Invoice overdue** check (hourly): flip `pending`→`overdue` past `due_date`.
- **Dashboard cache refresh** (every 5 min): precompute supervisor aggregates.

### 4.3 — Caching & Realtime (optional but recommended)
- Cache dashboard aggregates (in-process TTL cache for v1; Redis if available).
- Optional WebSocket/SSE channel to push new-ticket / SLA-breach / assignment events so queues update live.

---

## 🚀 Phase 5: Run & Developer Experience

### 5.1 — Backend run
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
Swagger at `http://localhost:8000/docs`. Configure CORS to allow `http://localhost:3000`.

### 5.2 — Frontend run
```powershell
cd frontend
npm run dev   # http://localhost:3000
```
`frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### 5.3 — Health & version endpoint
- `GET /health` → `{"status":"ok","version":"<app version>"}` — **unauthenticated**. Cheap (no DB round-trip required, or a fast `SELECT 1`).
- The dev launcher (§5.5) must **wait for `/health` to return 200** before starting the frontend, so the UI never boots against a dead API.

### 5.4 — API smoke-test file (`api.http` / Postman)
- Commit a `backend/api.http` (VS Code REST Client format) covering the key flows: register (bootstrap admin), register agent, login, `/auth/me`, change-password, create ticket, claim, comment, resolve, customer overview, record payment, KB search.
- Use a variable for the base URL and captured token so the file is runnable top-to-bottom. (Optionally also export a Postman collection `backend/TelecomCRM.postman_collection.json`.)
- This lets you verify the backend without the UI and gives Gemini a fast self-check harness.

### 5.5 — One-shot dev launcher (`run.ps1` + `run.bat`)
Script that: `docker compose up -d` → (first run) `alembic upgrade head` + seed (idempotent) → start uvicorn → **wait for `GET /health` = 200** → start `npm run dev`. Run backend and frontend in parallel; stream both logs. Document usage in `README.md`.

### 5.6 — README (`README.md`)
Write a concise, copy-pasteable README so the project runs in a few commands:
- One-paragraph **what this is** (CS-agent telecom CRM) + the 4 pillars.
- **Prerequisites**: Python 3.12, Node 18+, Docker.
- **Quick start** (the happy path):
  ```powershell
  # from repo root
  docker compose up -d
  cd backend; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  copy .env.example .env        # then edit if needed
  .\.venv\Scripts\python.exe -m alembic upgrade head
  .\.venv\Scripts\python.exe -m app.db.seed
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
  # new terminal:
  cd frontend; npm install; copy .env.local.example .env.local; npm run dev
  ```
  …or just `./run.ps1`.
- **First login**: open `http://localhost:3000`, click **Create account** — the first account becomes the **admin**; later accounts are agents.
- Links to `plan.md`, `memory.md`, `error.md`. Note seeded customers ≥ 100 and where to find seeded agent credentials (`memory.md`).

---

## ✅ Phase 6: Testing & Verification

1. **DB up**: `docker compose up -d`; `alembic upgrade head` succeeds; seed populates expected row counts (**verify customers ≥ 100**).
2. **First-run bootstrap**: on a fresh DB (no admin), register a user → it is created as **`admin`**. Register a second user → it is created as **`agent`**. A client trying to send `role: admin` on the second registration is ignored.
3. **API**: `/docs` loads; `POST /auth/login` returns tokens; protected routes 401 without token.
4. **Password rotation**: a user changes own password via `POST /auth/change-password` (wrong current password is rejected); an admin resets another user's password, that user is forced to rotate on next login (`must_change_password`).
5. **Login flow** (UI): login → redirect to dashboard; logout works; role guards hide admin-only nav for agents; `/register` works and self-assigns the right role.
6. **My Queue**: agent sees assigned tickets with correct SLA badges; claim from unassigned queue works.
7. **Ticket lifecycle**: create → comment (sets first_response_at) → reassign → escalate → resolve → close; audit log records each.
8. **SLA**: a ticket past its due time gets `sla_breached=true` after the sweep; badge turns red.
9. **Customer 360**: search finds a customer; overview shows subscriptions, billing summary, interactions, tickets in one view; "Log interaction" persists.
10. **Billing**: invoices listed; record payment flips status to paid.
11. **Plans**: 12 plans render with subscriber counts; add-ons visible.
12. **Knowledge Base**: search returns relevant articles fast; view count increments; link-to-ticket works.
13. **Users**: admin can create/edit/deactivate users and reset passwords.
14. **Multi-user**: two browsers, two agents → independent sessions; one agent's actions don't leak into the other's queue.

### Required automated tests (pytest + httpx, against a test DB)
These two cover the riskiest logic and **must** exist and pass:
1. **First-run bootstrap**: fresh DB → first register = `admin`; second register = `agent`; client-supplied `role` is ignored.
2. **Ticket lifecycle + SLA**: create (SLA due-times stamped) → first comment sets `first_response_at` → claim → escalate → resolve → close; invalid transition (e.g. `closed → in_progress`) is rejected (`CRM-TKT-002`); a past-due ticket is flagged `sla_breached` by the sweep.

Recommended (add if time permits): self password-change rejects a wrong current password; admin reset sets `must_change_password`; seed idempotency (running seed twice keeps customer count stable).

> **Conventions to assert/keep consistent:** all timestamps stored as UTC `timestamptz`; all money as `NUMERIC(10,2)` (never floats). SLA math runs in UTC.

---

## 📌 Execution Order (Follow This Exactly)

| Step | Phase | Description | Update memory.md |
|------|-------|-------------|:---:|
| 1 | 0.1 | Create monorepo structure | ✅ |
| 2 | 0.2 | docker-compose Postgres up | ✅ |
| 3 | 0.3 | Backend venv + deps | ✅ |
| 4 | 0.4 | Frontend scaffold (Next + shadcn) | ✅ |
| 5 | 1.1–1.7 | All SQLAlchemy models | ✅ |
| 6 | 1.8 | Alembic initial migration + upgrade | ✅ |
| 7 | 1.8 | Seed script + run seed | ✅ |
| 8 | 2.1 | Auth + security + deps | ✅ |
| 9 | 2.2 | Tickets API (core) | ✅ |
| 10 | 2.3–2.4 | Customers + interactions API | ✅ |
| 11 | 2.5 | Billing + plans API | ✅ |
| 12 | 2.6 | Knowledge base API | ✅ |
| 13 | 2.7–2.8 | Dashboard + users/audit API | ✅ |
| 14 | 3.1–3.2 | Theme + app shell + auth/login | ✅ |
| 15 | 3.3 | Dashboard / My Queue | ✅ |
| 16 | 3.4 | Tickets list + detail (core) | ✅ |
| 17 | 3.5 | Customer 360 | ✅ |
| 18 | 3.6–3.7 | Billing + plans pages | ✅ |
| 19 | 3.8 | Knowledge base pages | ✅ |
| 20 | 3.9 | Users + profile pages | ✅ |
| 21 | 4.1–4.3 | Pagination, indexes, SLA/overdue jobs, cache | ✅ |
| 22 | 5.3–5.4 | Health endpoint + `api.http` smoke file | ✅ |
| 23 | 5.5–5.6 | Run scripts (`run.ps1`/`run.bat`) + README quick-start | ✅ |
| 24 | 6.* | Required pytest tests (bootstrap + ticket lifecycle) + manual checklist | ✅ |

---

## 🚨 Rules for the Executor Agent

1. **ALWAYS** check `memory.md` before starting any work; **ALWAYS** update it after each step (what was done, errors, deviations).
2. **NEVER** store passwords in plaintext — hash with **bcrypt**.
3. **NEVER** use global mutable state — the API is stateless; all per-user state is in the JWT / DB.
4. Keep routers thin; business logic in `services/`. Keep code **typed** (Python type hints, TS strict).
5. Every list endpoint: **server-side pagination + filtering**. Never load full datasets client-side.
6. Test each module as you build it before moving on.
7. If an error blocks you for >2 attempts, **log it in `memory.md`** and move on, then return.
8. Secrets only via `.env`; commit `.env.example`, never real secrets.
9. Make the UI **demo-worthy** — colors, icons, spacing, motion, keyboard-friendly for agents.
10. Treat **Ticketing & SLA** and **Customer 360** as the two must-nail features; billing/plans/KB support them.
11. **Comment the code for readability.** Every module gets a short header docstring (its purpose). Every non-trivial function/class gets a docstring (what it does, args, returns). Add inline comments to explain *why* for any non-obvious logic — especially SLA math, the bootstrap role decision, ticket state transitions, and auth/token handling. Favor clear names over clever code. (TS: JSDoc on exported functions/components and complex hooks.)
12. **Maintain `error.md`.** Use a standardized error catalog (see §2.0). Whenever you define an application error code, or hit a setup/runtime error during execution, **add an entry to `error.md`** (code, meaning, cause, fix). Treat it as the troubleshooting companion to `memory.md`.

---

## ⚠️ Known Pitfalls (lessons carried over — apply proactively)

> These bit a prior build. They are stack-agnostic enough to matter here.

- **P1 — bcrypt vs passlib.** `passlib[bcrypt]` breaks against `bcrypt>=5` (`password cannot be longer than 72 bytes`). Use the `bcrypt` package directly for hashing/verification.
- **P2 — schedulers must start inside the app lifecycle.** Don't start APScheduler at import/module-load time (`RuntimeError: no running event loop`). Start it inside FastAPI's `lifespan` (or `@app.on_event("startup")`) and shut it down on shutdown.
- **P3 — don't pass live ORM objects across the session boundary.** Accessing attributes on a SQLAlchemy object after its session closes raises `DetachedInstanceError` / returns stale data. Convert to Pydantic/dicts before returning; in `get_current_user`, return serialized data, not a detached ORM row.
- **P4 — async session hygiene.** One `AsyncSession` per request via dependency; never share a session across requests/tasks; always `await session.close()` (let the dependency handle it). Background jobs create their own short-lived sessions.
- **P5 — CORS.** Frontend on `:3000`, API on `:8000` — configure `CORSMiddleware` with the explicit origin and `allow_credentials` as needed, or auth/cookies will silently fail.
- **P6 — token refresh on the client.** Centralize fetch in `lib/api.ts`: on 401, try the refresh token once, then redirect to login. Avoid scattering auth logic across components.
- **P7 — timestamps in UTC.** Store `timestamptz` in UTC; format to local time only in the UI. SLA math must be UTC to be correct.
