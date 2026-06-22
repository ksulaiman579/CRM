# 🚑 Telecom CRM — Error Catalog & Troubleshooting

> Companion to `plan.md` (what to build) and `memory.md` (what's done).
> **Two parts:**
> 1. **Application error codes** returned by the API (the `CRM-<DOMAIN>-<NNN>` scheme from `plan.md` §2.0).
> 2. **Setup / runtime troubleshooting** — errors you hit while building or running, with fixes.
>
> **Executor rule:** whenever you define a new error code, or hit a new setup/runtime error, **add a row here** (and link it from `memory.md`'s Issues table). Keep codes stable once assigned.

---

## 1. Application Error Codes

All errors use the envelope:

```json
{ "error": { "code": "CRM-AUTH-002", "message": "Invalid username or password", "detail": null } }
```

Domains: `AUTH, USER, CUST, TKT, SLA, BILL, PLAN, KB, DASH, SYS`.

### AUTH — authentication & registration
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-AUTH-001 | 400 | Registration validation failed | Missing/short password, bad email | Return field errors; enforce strength rule |
| CRM-AUTH-002 | 401 | Invalid credentials | Wrong username/password | Generic message (don't reveal which) |
| CRM-AUTH-003 | 409 | Username or email already taken | Duplicate on register | Ask user to pick another / log in |
| CRM-AUTH-004 | 401 | Token expired | Access token past TTL | Client calls `/auth/refresh` once, then retry |
| CRM-AUTH-005 | 401 | Token invalid / malformed | Bad signature, tampering | Force re-login |
| CRM-AUTH-006 | 403 | Account deactivated | `is_active = false` | Admin must reactivate |
| CRM-AUTH-007 | 403 | Password change required | `must_change_password = true` | Redirect to change-password screen |
| CRM-AUTH-008 | 400 | Current password incorrect | Wrong current pw on change | Re-prompt |

### USER — user management (admin)
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-USER-001 | 403 | Insufficient role | Non-admin hit admin route | Gate via `require_role('admin')` |
| CRM-USER-002 | 404 | User not found | Bad id | Validate id |
| CRM-USER-003 | 409 | Cannot deactivate last admin | Removing the only admin | Block; require another admin first |

### CUST — customers
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-CUST-001 | 404 | Customer not found | Bad id | Validate id |
| CRM-CUST-002 | 409 | Duplicate account_number / national_id | Unique violation | Surface conflict field |

### TKT — tickets
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-TKT-001 | 404 | Ticket not found | Bad id | Validate id |
| CRM-TKT-002 | 409 | Invalid status transition | e.g. `closed → in_progress` | Enforce allowed transitions in `ticket_service` |
| CRM-TKT-003 | 409 | Ticket already assigned | Two agents claim at once | **Implemented**: `POST /tickets/{id}/claim` does a conditional `UPDATE … WHERE assigned_agent_id IS NULL`; loser of the race gets this code |
| CRM-TKT-004 | 422 | Missing required field on create | No customer/subject/category | Validate before insert |
| CRM-TKT-005 | 409 | Stale write (optimistic concurrency) | Tab held an out-of-date `version` | Client reloads ticket and retries; `version` token sent on every PATCH |

### SLA — sla policies & timers
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-SLA-001 | 404 | No SLA policy for priority | Policy not seeded | Seed all 4 priorities; fall back to default |

### BILL — billing
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-BILL-001 | 404 | Invoice not found | Bad id | Validate id |
| CRM-BILL-002 | 409 | Invoice already paid | Double payment | Block re-payment; show status |
| CRM-BILL-003 | 422 | Payment exceeds balance | Over-payment | Validate amount ≤ outstanding |

### PLAN / KB / DASH
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-PLAN-001 | 404 | Plan/addon not found | Bad id | Validate id |
| CRM-KB-001 | 404 | Article not found | Bad id/slug | Validate |
| CRM-KB-002 | 409 | Duplicate slug | Title collision | Append suffix |
| CRM-DASH-001 | 500 | Aggregate computation failed | Bad query / null data | Guard nulls; log and return safe zeros |

### SYS — framework / unexpected
| Code | HTTP | Meaning | Likely cause | Fix |
|------|------|---------|--------------|-----|
| CRM-SYS-401 | 401 | Not authenticated | Missing token | Send `Authorization: Bearer` |
| CRM-SYS-403 | 403 | Forbidden | Role/ownership check failed | Check permissions |
| CRM-SYS-422 | 422 | Request validation error | Pydantic validation | Return field-level details |
| CRM-SYS-429 | 429 | Rate limited (if enabled) | Too many requests | Back off |
| CRM-SYS-500 | 500 | Unexpected server error | Unhandled exception | Log traceback; never leak internals |

> Add new codes above as features grow. Keep the frontend's friendly-message map in sync with this table.

---

## 2. Setup / Runtime Troubleshooting

These are environment and framework gotchas. The first batch mirrors the **Known Pitfalls (P1–P7)** in `plan.md` — pre-loaded so you can search by symptom.

| ID | Symptom / error | Cause | Fix |
|----|-----------------|-------|-----|
| ERR-ENV-01 | `password cannot be longer than 72 bytes` during hashing | `passlib[bcrypt]` breaks with `bcrypt>=5` | Use the `bcrypt` package directly (P1) |
| ERR-ENV-02 | `RuntimeError: no running event loop` at startup | APScheduler started at import time | Start scheduler inside FastAPI `lifespan`, stop on shutdown (P2) |
| ERR-ENV-03 | `DetachedInstanceError` / stale attributes | ORM object used after its session closed | Convert to Pydantic/dict before returning; don't return live ORM rows (P3) |
| ERR-ENV-04 | Intermittent "session already closed" / cross-request data bleed | Sharing one `AsyncSession` across requests/tasks | One session per request via dependency; background jobs open their own (P4) |
| ERR-ENV-05 | Browser blocks API calls / `CORS` error in console | CORS origin not allowed | Configure `CORSMiddleware` with `http://localhost:3000`, `allow_credentials` as needed (P5) |
| ERR-ENV-06 | User logged out randomly / 401 loops | No central token refresh | Centralize refresh-on-401 in `lib/api.ts`, redirect to login after one failed refresh (P6) |
| ERR-ENV-07 | SLA timers off by hours | Mixing local time and UTC | Store `timestamptz` in UTC; convert only in the UI (P7) |
| ERR-DB-01 | `connection refused` to Postgres | DB container not up / wrong port | `docker compose up -d`; verify `5432`; check `DATABASE_URL` |
| ERR-DB-02 | `password authentication failed` | `.env` creds ≠ compose creds | Align `backend/.env` with `docker-compose.yml` |
| ERR-DB-03 | Alembic: "target database is not up to date" | Pending migration | `alembic upgrade head` before running the app |
| ERR-DB-04 | Async driver error / `dialect ... psycopg2` | Sync URL with async engine | Use `postgresql+asyncpg://...` in `DATABASE_URL` |
| ERR-FE-01 | `NEXT_PUBLIC_API_URL is undefined` | Missing env var | Set it in `frontend/.env.local`, restart `next dev` |
| ERR-FE-02 | Hydration mismatch warnings | Reading tokens/`window` during SSR | Guard browser-only code; gate behind `useEffect`/client components |

### Template for new entries

```
| ERR-<AREA>-NN | <symptom> | <root cause> | <fix> |
```
Also mirror anything significant into `memory.md` → "Issues & Blockers" with severity and status.
