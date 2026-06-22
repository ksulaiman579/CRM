# Telecom CRM — V2 Implementation Plan (Full CRM, Executive UI)

> Supersedes the original `plan.md` for V2 scope. `plan.md` remains the record of the V1 build.
> Decisions locked: **Full CRM suite**, **PostgreSQL**, **single fixed superuser (`admin`/`admin`, demo-only)**, **executive light-theme UI** modeled on the supplied reference screenshots.

---

## 0. Guiding principles

- **Multi-agent safe by default** — every write is concurrency-correct; no blind overwrites.
- **CRM, not a ticket tool** — accounts, contacts, sales pipeline, activities, campaigns, analytics; ticketing is one module among several.
- **One product feel** — a single design system applied across every screen (per reference shots).
- **Lived-in demo data** — 120+ customers and all surrounding records, idempotently seeded.

---

## 1. Design system (from reference screenshots)

### 1.1 Tokens — `frontend/src/styles/tokens.css`
| Token | Value | Use |
|-------|-------|-----|
| `--bg-app` | `#F6F4EF` (warm cream) | app background |
| `--bg-surface` | `#FFFFFF` | cards, panels |
| `--bg-invert` | `#111111` | primary buttons, selected cards |
| `--accent` | `#111111` | primary actions (black, per refs) |
| `--cat-blue / teal / yellow / dark` | pastels | category tags on cards only |
| `--text-strong / muted / faint` | `#111 / #6B6B6B / #9A9A9A` | type hierarchy |
| `--radius-card` | `20px` | cards |
| `--radius-pill` | `999px` | buttons, chips |
| `--shadow-soft` | `0 4px 24px rgba(0,0,0,.06)` | card elevation |
| spacing scale | 4 / 8 / 12 / 16 / 24 / 32 | layout rhythm |
| type scale | 12 / 14 / 16 / 20 / 28 / 36 | hierarchy |

**Dark mode is in scope.** All colors are defined as CSS variables on `:root` (light) with a `[data-theme="dark"]` override block: `--bg-app` → near-black `#0E0E10`, `--bg-surface` → `#17171A`, `--bg-invert`/`--accent` flip to white for primary CTAs, text tokens lighten, shadows deepen, category pastels desaturate slightly. Theme stored in `localStorage` + system-preference default, toggled from the topbar/profile menu, applied via `data-theme` on `<html>` (no flash-of-wrong-theme: inline script sets it pre-hydration). Every component reads tokens only — never hard-coded colors — so both themes come for free.

### 1.2 Component kit — `frontend/src/components/ui/`
`AppShell` (sidebar + topbar), `Sidebar` (grouped nav + Members block w/ avatars), `Topbar` (⌘K search, filters, sort, dark CTA), `StatTile`, `KpiStrip`, `Card`, `KanbanBoard` + `KanbanColumn` + `KanbanCard`, `DetailPanel` (right drawer, editable field rows w/ pencil), `AvatarStack`, `StatusPill`, `PriorityTag`, `CountChip`, `DataTable` (saved filters, inline actions, skeleton), `CalendarWidget`, charts (`BarMini`, `RadialGauge`, `LineTrend`) via Recharts, `Drawer`, `Modal`, `Toast`.

### 1.3 Screen blueprints
- **Dashboard (role-aware):** KPI strip → for agents: *My Day* tasks + *My Queue*; supervisors: floor view (agents online, queue depth, SLA breaching-soon, CSAT gauge); superuser: system + user mgmt entry.
- **Customers list:** topbar search + filters + "Add customer" dark pill; KPI band (new customers bar chart, success radial gauge, counts); switchable **table** / **kanban-by-segment**.
- **Customer 360:** left = account header + KPIs + colored interaction-history cards (avatar stacks); right = `DetailPanel` profile with editable fields + quick actions (call/SMS/email/note); tabs: Subscriptions, Billing, Tickets, Opportunities, Interactions, Notes.
- **Sales pipeline:** kanban (Lead→Qualified→Proposal→Won/Lost) with value chips, owner avatars, due dates; "Stage Funnel" totals panel.
- **Tickets:** queue/my/team boards + table; SLA countdowns; claim/Take-next; per-ticket presence banner.
- **Activities/Tasks:** calendar + board (Backlog/In progress/Done) like ref #3; burndown-style trend.
- **Campaigns, Analytics, KB, Billing, Plans, Admin/Users** follow the same shell.

---

## 2. Phase 0 — Fixed superuser & provisioning

**Backend**
- `app/db/seed.py`: seed one `superuser` — username `admin`, password `admin`, `role="superuser"`, `must_change_password=False`. Documented demo-only.
- `app/models/user.py`: add `superuser` to role set; keep `team_id`, `is_active`, `must_change_password`.
- `app/core/deps.py`: `require_role(...)` supporting `superuser > supervisor > agent`; add `get_current_superuser`.
- `app/api/v1/auth.py`: **remove public register**; keep login/refresh/change-password.
- `app/api/v1/users.py`: superuser-only CRUD — create user (assign role+team), reset password (forces `must_change_password`), activate/deactivate, list/search. Guard `CRM-USER-003` (last superuser).

**Frontend**
- Remove `(auth)/register`; add `(app)/admin/users` provisioning screen (table + create/edit drawer + reset-password action), visible only to superuser.
- Update README, `memory.md`, credentials table to `admin`/`admin`.

---

## 3. Phase 1 — Concurrency safety + Postgres

- **Postgres:** `app/config.py` + `.env` → `postgresql+asyncpg://...`; `docker-compose.yml` Postgres 16; run existing Alembic migrations; seed against PG. SQLite kept only as dev fallback flag.
- **Atomic claim:** `app/api/v1/tickets.py` → `POST /tickets/{id}/claim` and `/release` using conditional `UPDATE ... WHERE assigned_agent_id IS NULL`; 0 rows → `CRM-TKT-003`. Replace blind `assigned_agent_id` overwrite in `PATCH`.
- **AuthZ on mutations:** new `assert_can_edit_ticket()` — agent: own/claimed only; supervisor: own team; superuser: all.
- **Optimistic concurrency:** add `version` (or `updated_at`) col + migration; `PATCH` checks it → 409 `CRM-TKT-004` on stale write.
- **Per-ticket presence:** extend `app/core/events.py` + SSE with `ticket_viewing`/`ticket_released`; frontend banner on `tickets/[id]`.
- Add new codes to `error.md`; mirror to `memory.md` issues table.

---

## 4. Phase 2 — Full CRM modules

Each module = model + migration + schema + router + seed + UI screen, all on the design system.

| # | Module | Backend (new files) | Frontend |
|---|--------|---------------------|----------|
| 2.1 | **Accounts & Contacts** | `models/account.py`, `models/contact.py`, `schemas/`, `api/v1/accounts.py`, `contacts.py` | Customers list (table+kanban-by-segment), Customer 360 rebuild |
| 2.2 | **Sales pipeline** | `models/opportunity.py`, `api/v1/opportunities.py` (stage transitions, value, owner) | Pipeline kanban + Stage Funnel panel |
| 2.3 | **Activities & Tasks** | `models/activity.py`, `api/v1/activities.py` (calls/follow-ups/reminders, due, assignee) | Calendar + board + "My Day" |
| 2.4 | **Omnichannel timeline** | extend `models/interaction` (channel: call/sms/email/chat), `api/v1/interactions.py` | Unified timeline tab in 360 |
| 2.5 | **Campaigns** | `models/campaign.py`, `api/v1/campaigns.py` (target list, outcomes) | Campaigns list + detail |
| 2.6 | **Notes & attachments** | `models/note.py`, `models/attachment.py`, upload endpoint (local disk for demo) | Notes tab, attach control |
| 2.7 | **Reporting & Analytics** | `api/v1/analytics.py` — pipeline value, SLA compliance, CSAT trend, agent productivity, revenue-at-risk (cached via existing scheduler) | Analytics dashboard (bar/gauge/line) |

Cross-link everything from the account view. Reuse existing SLA, Billing, Plans, KB, CSAT.

---

## 5. Phase 3 — Seed data (idempotent, deterministic)

`app/db/seed.py` rewrite (Faker, fixed seed, re-run safe):
- 1 superuser (`admin`), 3 supervisors, ~10 agents, 3 teams.
- **120 accounts** (consumer/SME/enterprise mix), 1–4 contacts each, addresses, segment, lifetime value.
- Per account: subscriptions, invoices (subset overdue), payments, devices, interaction history across all 4 channels.
- ~200 tickets across statuses/priorities/channels w/ comments, SLA timers (some breaching), CSAT on resolved.
- ~60 opportunities across pipeline stages w/ realistic values.
- Activities/tasks per agent (past-due + upcoming).
- 3–4 campaigns, 12 plans/addons, 40 KB articles.

---

## 6. Phase 4 — Apply design system across all screens

Build the kit (§1.2) early in Phase 2 so each module ships styled. Final pass: ⌘K command palette + wire the dead global search, role-aware dashboard, skeleton loaders, empty states, consistent charts, light theme polish.

---

## 7. Execution order

```
P0 Superuser + provisioning      (identity foundation)
P1 Concurrency + Postgres        (safety; do before load)
P3 Seed data                     (so P2/P4 render real data)
P2 Full-CRM modules              (build kit first, then module-by-module, styled)
P4 Design polish pass            (command palette, dashboards, consistency)
```

## 8. New error codes to register in `error.md`
- `CRM-TKT-005` 409 — stale write (optimistic concurrency). *(TKT-004 was already taken; used 005.)*
- `CRM-OPP-001/002`, `CRM-ACCT-001`, `CRM-CONT-001`, `CRM-ACT-001`, `CRM-CAMP-001` — not-found / validation per new module.

---

## 9. Build status

- **Phase 0 — DONE.** Fixed superuser (`admin`/`admin`), public registration removed, role hierarchy + provisioning API/UI, docs updated.
- **Phase 1 — DONE (code; runtime verification pending env).**
  - Postgres/Supabase wiring: `config.py` (DB_SSL, statement-cache toggle), `session.py` (asyncpg connect_args, pool_pre_ping), `.env.example` (Supabase pooler guidance), Alembic driven by `settings.DATABASE_URL`.
  - Atomic `POST /tickets/{id}/claim` + `/release` (conditional UPDATE, CRM-TKT-003 on race).
  - Authorization on ticket mutations (`assert_can_edit_ticket`).
  - Optimistic concurrency: `tickets.version` column + migration `a1c2e3f4b5d6`, `version` token on PATCH, CRM-TKT-005 on stale write.
  - Per-ticket presence via SSE (`ticket_viewing`/`ticket_released`); frontend collision banner + version-aware updates + claim/release/conflict UI.
  - Tests updated to the provisioned-account model (`tests/_helpers.py`, seeded superuser in `conftest.py`); **not yet executed** — no local venv/pytest. Run in CI/Supabase.
- **Phase 3 (light slice) — DONE.** Idempotent `--reset` seed; 120 customers / 200 tickets; live on Supabase.
- **Phase 2 — IN PROGRESS** (Contact Center folded in). Build order: (1) functional teams + agent status ✅, (2) Accounts/Contacts, (3) Sales pipeline, (4) Activities/Tasks, (5) Contact-Center call simulator, (6) Campaigns/Notes/Analytics.
  - **2.5 (Contact Center) backend DONE:** `calls` table (migration `d4f5a6b7c8e9`, RLS on), ACD in `app/core/acd.py` (templated synthetic calls, intent→team routing, distribute to longest-idle ready agent), generator job every 45s (capped 15), `app/api/v1/calls.py` (list/get/generate/answer/complete, raise-ticket-from-call), going 'ready' pulls a queued call, SSE events (call_queued/offered/answered/completed). Seeds 50 historical calls. Full loop verified live (agent ready→offered→answer→complete→ticket). **UI still pending.**
  - **2.1 DONE:** 5 functional teams (Sales, Complaints, Call Center, Technical, Billing) with `Team.code`; skill-based routing (`app/core/routing.py`, category→team) on ticket create + seed; agent presence `User.status` (ready/on_call/wrap_up/break/lunch/restroom/meeting/offline) via `POST /users/me/status` + SSE `agent_status_changed`. Migration `c3e4f5a6b7d8`. Verified live.
- Then **Phase 4** dark/light executive UI polish.
