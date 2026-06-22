# Graph Report - CRM  (2026-06-22)

## Corpus Check
- 98 files · ~40,717 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 620 nodes · 1001 edges · 42 communities (38 shown, 4 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 233 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74a936d7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 40|Community 40]]

## God Nodes (most connected - your core abstractions)
1. `AppError` - 25 edges
2. `Base` - 23 edges
3. `User` - 22 edges
4. `📝 Step-by-Step Log` - 22 edges
5. `useAuth()` - 21 edges
6. `Ticket` - 19 edges
7. `FastAPI` - 18 edges
8. `Customer` - 16 edges
9. `fetchWithAuth()` - 16 edges
10. `compilerOptions` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Connection` --uses--> `Base`  [INFERRED]
  backend/alembic/env.py → backend/app/db/base.py
- `AppError` --uses--> `AppError`  [INFERRED]
  backend/app/main.py → backend/app/core/errors.py
- `LoginRequest` --uses--> `AppError`  [INFERRED]
  backend/app/api/v1/auth.py → backend/app/core/errors.py
- `AsyncSession` --uses--> `AppError`  [INFERRED]
  backend/app/api/v1/auth.py → backend/app/core/errors.py
- `TokenRefreshRequest` --uses--> `AppError`  [INFERRED]
  backend/app/api/v1/auth.py → backend/app/core/errors.py

## Import Cycles
- 1-file cycle: `backend/app/main.py -> backend/app/main.py`
- 1-file cycle: `backend/app/core/sla.py -> backend/app/core/sla.py`

## Communities (42 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (54): BaseModel, check_sla_breach(), Returns True if the ticket has breached either response or resolution SLA., datetime, ChangePasswordRequest, Config, LoginRequest, RegisterRequest (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (32): AsyncSession, Call, AsyncSession, abandon_stale_calls(), distribute_call(), find_any_ready_agent(), _find_ready_agent(), generate_call() (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (36): AsyncSession, AsyncSession, AsyncSession, CustomerCreate, Base, _kb_body(), seed_data(), DeclarativeBase (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (26): AdminPasswordReset, AdminUserCreate, AsyncSession, AsyncSession, ChangePasswordRequest, create_access_token(), create_refresh_token(), hash_password() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (23): AppLayout(), NAV, COLORS, DashboardPage(), ChangePasswordPage(), AgentStatusControl(), OPTIONS, STATUS_META (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (43): AsyncSession, Call, AsyncSession, AsyncClient, CallComplete, AppError, broadcast_event(), clear_viewer() (+35 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (28): 🔑 Credentials (for local testing only), 🔄 Deviations from Plan, 🗂️ Environment Facts (fill in as discovered), 📊 Overall Progress, 🧭 Quick Context (read first), Step 10 — Phase 2 API Implementation (Dashboard & Tickets), Step 11 — Phase 3 Frontend Integration (Dashboard & Tickets), Step 12 — Phase 2 API Implementation (Customer 360 & Interactions) (+20 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (39): dependencies, class-variance-authority, clsx, date-fns, lucide-react, next, @radix-ui/react-avatar, @radix-ui/react-dialog (+31 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (14): 0. Guiding principles, 1.1 Tokens — `frontend/src/styles/tokens.css`, 1.2 Component kit — `frontend/src/components/ui/`, 1.3 Screen blueprints, 1. Design system (from reference screenshots), 2. Phase 0 — Fixed superuser & provisioning, 3. Phase 1 — Concurrency safety + Postgres, 4. Phase 2 — Full CRM modules (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (12): 1. Application Error Codes, 2. Setup / Runtime Troubleshooting, AUTH — authentication & registration, BILL — billing, CUST — customers, PLAN / KB / DASH, SLA — sla policies & timers, SYS — framework / unexpected (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (18): AsyncSession, AsyncSession, AsyncSession, get_current_user(), decode_token(), FastAPI, KbArticleCreate, AgentDashboard (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (13): aliases, components, utils, rsc, $schema, style, tailwind, baseColor (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.20
Nodes (10): 2.0 — Error Handling & Error Codes (do this first), 2.1 — Auth & Security (`core/security.py`, `api/v1/auth.py`), 2.2 — Tickets API (`api/v1/tickets.py`) — CORE, 2.3 — Customers API (`api/v1/customers.py`) — Customer 360, 2.4 — Interactions API (`api/v1/interactions.py`), 2.5 — Billing & Plans APIs, 2.6 — Knowledge Base API (`api/v1/kb.py`), 2.7 — Dashboard API (`api/v1/dashboard.py`) (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (23): any, AsyncClient, AsyncClient, AsyncClient, AsyncClient, A simple thread-safe, in-memory TTL Cache., TTLCache, Background job to check all active tickets and flag them if they have breached t (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.20
Nodes (10): 3.1 — Design System & Theme (`globals.css`, `tailwind.config.ts`), 3.2 — App Shell & Auth (`app/(app)/layout.tsx`, `lib/auth.ts`), 3.3 — Dashboard / My Queue (`app/(app)/page.tsx`) — agent landing, 3.4 — Tickets (`tickets/page.tsx`, `tickets/[id]/page.tsx`) — CORE, 3.5 — Customer 360 (`customers/page.tsx`, `customers/[id]/page.tsx`), 3.6 — Billing (`billing/page.tsx`), 3.7 — Plans (`plans/page.tsx`), 3.8 — Knowledge Base (`kb/page.tsx`, `kb/[id]/page.tsx`) (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (9): Account model — first-run bootstrap (decided), 📌 Execution Order (Follow This Exactly), ⚠️ Known Pitfalls (lessons carried over — apply proactively), ✅ Phase 6: Testing & Verification, 🎯 Project Overview, Required automated tests (pytest + httpx, against a test DB), 🚨 Rules for the Executor Agent, Tech Stack (decided) (+1 more)

### Community 17 - "Community 17"
Cohesion: 0.54
Nodes (7): AsyncSession, InvoiceCreate, PaymentCreate, create_invoice(), create_payment(), get_invoice(), list_invoices()

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (4): inter, metadata, Providers(), Toast

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (8): 1. Launch the Application, 2. Authentication & Account Provisioning, 3. Dummy Data Credentials, ⚡ Quick Start (Portable Windows Execution), 🛠 Tech Stack, 🚀 Telecom Customer-Service CRM, 🧪 Testing the API, 🌟 The Four Pillars

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (18): do_run_migrations(), run_async_migrations(), run_migrations_online(), Config, Settings, app_error_handler(), global_exception_handler(), lifespan() (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (7): 1. Backend → Render, 2. Frontend → Vercel, 3. Wire CORS back, After this, Connection string to use for the deployed backend, Deploying off your PC (Render + Vercel + Supabase), Notes

### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (9): 1.1 — Users, Teams, Audit (`models/user.py`), 1.2 — Customers & Interactions (`models/customer.py`), 1.3 — Services: Subscriptions & Devices (`models/service.py`), 1.4 — Plans & Add-ons (`models/plan.py`), 1.5 — Billing (`models/billing.py`), 1.6 — Tickets & SLA (`models/ticket.py`) — CORE, 1.7 — Knowledge Base (`models/kb.py`), 1.8 — Migrations & Seed Data (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (7): 5.1 — Backend run, 5.2 — Frontend run, 5.3 — Health & version endpoint, 5.4 — API smoke-test file (`api.http` / Postman), 5.5 — One-shot dev launcher (`run.ps1` + `run.bat`), 5.6 — README (`README.md`), 🚀 Phase 5: Run & Developer Experience

### Community 33 - "Community 33"
Cohesion: 0.40
Nodes (5): 0.1 — Repository Structure, 0.2 — Local Database (Docker Compose), 0.3 — Backend Dependencies, 0.4 — Frontend Scaffolding, 📁 Phase 0: Environment & Scaffolding

### Community 34 - "Community 34"
Cohesion: 0.50
Nodes (4): 4.1 — Multi-User & Concurrency, 4.2 — Background Jobs, 4.3 — Caching & Realtime (optional but recommended), ⚡ Phase 4: Performance, Multi-User & Background Jobs

## Knowledge Gaps
- **194 isolated node(s):** `Config`, `any`, `Config`, `Config`, `Config` (+189 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 11`, `Community 14`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `FastAPI` connect `Community 11` to `Community 2`, `Community 3`, `Community 5`, `Community 17`, `Community 20`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `AppError` connect `Community 5` to `Community 11`, `Community 3`, `Community 20`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `AppError` (e.g. with `AdminPasswordReset` and `AdminUserCreate`) actually correct?**
  _`AppError` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Base` (e.g. with `Connection` and `Invoice`) actually correct?**
  _`Base` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `User` (e.g. with `AdminPasswordReset` and `AdminUserCreate`) actually correct?**
  _`User` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `# NOTE: Public self-registration has been removed. Accounts are provisioned by`, `Manually inject a simulated inbound call (handy for demos/testing).      With mi`, `Switch a customer's subscription to a different plan and log the action     as a` to the rest of the system?**
  _227 weakly-connected nodes found - possible documentation gaps or missing edges._