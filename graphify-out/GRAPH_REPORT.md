# Graph Report - CRM  (2026-06-22)

## Corpus Check
- 82 files · ~30,634 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 489 nodes · 751 edges · 38 communities (35 shown, 3 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 176 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

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
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]

## God Nodes (most connected - your core abstractions)
1. `Base` - 22 edges
2. `📝 Step-by-Step Log` - 22 edges
3. `useAuth()` - 21 edges
4. `AppError` - 20 edges
5. `FastAPI` - 17 edges
6. `User` - 16 edges
7. `compilerOptions` - 16 edges
8. `seed_data()` - 14 edges
9. `Ticket` - 14 edges
10. `AsyncSession` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Connection` --uses--> `Base`  [INFERRED]
  backend/alembic/env.py → backend/app/db/base.py
- `Device` --uses--> `Base`  [INFERRED]
  backend/app/models/service.py → backend/app/db/base.py
- `create_invoice()` --calls--> `Invoice`  [INFERRED]
  backend/app/api/v1/billing.py → backend/app/models/billing.py
- `create_payment()` --calls--> `Payment`  [INFERRED]
  backend/app/api/v1/billing.py → backend/app/models/billing.py
- `AsyncSession` --uses--> `Ticket`  [INFERRED]
  backend/app/api/v1/customers.py → backend/app/models/ticket.py

## Import Cycles
- 1-file cycle: `backend/app/main.py -> backend/app/main.py`
- 1-file cycle: `backend/app/core/sla.py -> backend/app/core/sla.py`

## Communities (38 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (47): BaseModel, ChangePasswordRequest, Config, LoginRequest, RegisterRequest, TokenRefreshRequest, TokenResponse, UserResponse (+39 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (28): 🔑 Credentials (for local testing only), 🔄 Deviations from Plan, 🗂️ Environment Facts (fill in as discovered), 📊 Overall Progress, 🧭 Quick Context (read first), Step 10 — Phase 2 API Implementation (Dashboard & Tickets), Step 11 — Phase 3 Frontend Integration (Dashboard & Tickets), Step 12 — Phase 2 API Implementation (Customer 360 & Interactions) (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (38): AsyncSession, AsyncSession, AsyncSession, AsyncClient, AsyncClient, CustomerCreate, Base, seed_data() (+30 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (34): AdminPasswordReset, AdminUserCreate, app_error_handler(), global_exception_handler(), AppError, AsyncSession, AsyncSession, AsyncSession (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (15): AppLayout(), COLORS, DashboardPage(), ChangePasswordPage(), Customer360Page(), KbArticle, TicketComment, TicketDetailPage() (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (27): AsyncSession, AsyncClient, broadcast_event(), Broadcasts an event payload to all connected clients., Background job to check all active tickets and flag them if they have breached t, sweep_sla_breaches(), check_sla_breach(), compute_sla_due_dates() (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (12): 1. Application Error Codes, 2. Setup / Runtime Troubleshooting, AUTH — authentication & registration, BILL — billing, CUST — customers, PLAN / KB / DASH, SLA — sla policies & timers, SYS — framework / unexpected (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (21): dependencies, class-variance-authority, clsx, date-fns, lucide-react, next, @radix-ui/react-avatar, @radix-ui/react-dialog (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (18): devDependencies, autoprefixer, eslint, eslint-config-next, postcss, tailwindcss, @types/node, @types/react (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.50
Nodes (3): Config, Settings, BaseSettings

### Community 11 - "Community 11"
Cohesion: 0.15
Nodes (13): lifespan(), AsyncSession, Background job to check pending invoices and flag them as overdue if past the du, Register all background jobs to the provided scheduler instance., Precomputes supervisor dashboard metrics and populates the cache to keep it warm, refresh_dashboard_cache(), setup_scheduler(), sweep_overdue_invoices() (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (13): aliases, components, utils, rsc, $schema, style, tailwind, baseColor (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.20
Nodes (10): 2.0 — Error Handling & Error Codes (do this first), 2.1 — Auth & Security (`core/security.py`, `api/v1/auth.py`), 2.2 — Tickets API (`api/v1/tickets.py`) — CORE, 2.3 — Customers API (`api/v1/customers.py`) — Customer 360, 2.4 — Interactions API (`api/v1/interactions.py`), 2.5 — Billing & Plans APIs, 2.6 — Knowledge Base API (`api/v1/kb.py`), 2.7 — Dashboard API (`api/v1/dashboard.py`) (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.25
Nodes (3): any, A simple thread-safe, in-memory TTL Cache., TTLCache

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
Cohesion: 0.52
Nodes (6): AsyncSession, KbArticleCreate, create_article(), get_article(), list_articles(), list_categories()

### Community 20 - "Community 20"
Cohesion: 0.40
Nodes (4): do_run_migrations(), run_async_migrations(), run_migrations_online(), Connection

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (3): AsyncClient, test_first_run_bootstrap(), test_password_rotation_and_resets()

### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (9): 1.1 — Users, Teams, Audit (`models/user.py`), 1.2 — Customers & Interactions (`models/customer.py`), 1.3 — Services: Subscriptions & Devices (`models/service.py`), 1.4 — Plans & Add-ons (`models/plan.py`), 1.5 — Billing (`models/billing.py`), 1.6 — Tickets & SLA (`models/ticket.py`) — CORE, 1.7 — Knowledge Base (`models/kb.py`), 1.8 — Migrations & Seed Data (+1 more)

### Community 31 - "Community 31"
Cohesion: 0.22
Nodes (8): 1. Launch the Application, 2. First-Run Bootstrap & Authentication, 3. Dummy Data Credentials, ⚡ Quick Start (Portable Windows Execution), 🛠 Tech Stack, 🚀 Telecom Customer-Service CRM, 🧪 Testing the API, 🌟 The Four Pillars

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
- **167 isolated node(s):** `Config`, `any`, `Config`, `Config`, `Config` (+162 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Community 5` to `Community 11`, `Community 0`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `FastAPI` connect `Community 3` to `Community 2`, `Community 5`, `Community 11`, `Community 17`, `Community 19`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Base` connect `Community 2` to `Community 3`, `Community 20`, `Community 5`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `Base` (e.g. with `Connection` and `Invoice`) actually correct?**
  _`Base` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Server-Sent Events streaming endpoint.     Clients connect passing their JWT tok`, `Config`, `any` to the rest of the system?**
  _177 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05723905723905724 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06896551724137931 - nodes in this community are weakly interconnected._