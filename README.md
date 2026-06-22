# 🚀 Telecom Customer-Service CRM

A high-performance, production-grade Customer Relationship Management (CRM) application built specifically for Telecom Customer Service Agents. Designed to handle high-stress environments where agents need instant access to customer data, SLA-backed ticketing, billing tools, and knowledge base articles—all on a single screen.

## 🌟 The Four Pillars

1. **Ticketing & SLA** — Case management with priority queues, automatic assignment, and live SLA countdowns.
2. **Customer 360** — A single-pane-of-glass showing the customer's profile, active subscriptions, devices, billing status, and full interaction history.
3. **Knowledge Base** — Searchable troubleshooting guides and SOPs that agents can reference while on calls.
4. **Billing & Plans** — Access to the active catalog of telecom services and the ability to track and manage overdue invoices.

## 🛠 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), SQLite (with aiosqlite), APScheduler for background jobs.
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query.
- **Security**: Stateless JWT Authentication, bcrypt password hashing, Role-Based Access Control (Admin, Supervisor, Agent).

---

## ⚡ Quick Start (Portable Windows Execution)

This repository has been configured to run easily in a Windows environment without the need for Docker or global dependencies.

### 1. Launch the Application

Simply double-click the `run.bat` file in the root directory, or execute the PowerShell script directly:

```powershell
.\run.ps1
```

This one-shot launcher will:
- Boot the FastAPI backend in a background process.
- Wait for the API health checks to clear.
- Boot the Next.js frontend and open it in your browser.

*Note: The backend runs on `http://localhost:8000` and the frontend runs on `http://localhost:3000`.*

### 2. Authentication & Account Provisioning

Public self-registration is **disabled**. The CRM ships with a single fixed
**superuser** who provisions every other account:

- **Superuser**: `admin` (Password: `admin`)

> ⚠️ **Demo only.** This is a generic, well-known credential intended for local
> evaluation — this build is not meant to be deployed. Change it before any real use.

The superuser can create agents/supervisors, assign teams, reset passwords, and
activate/deactivate accounts from **Manage Users** (`/users`). Provisioned users
are required to set their own password on first login.

### 3. Dummy Data Credentials

The database is heavily pre-seeded with 110 Customers, 150 Tickets, 12 Plans, and 40 KB Articles.
It also includes pre-seeded agents and supervisors to ensure the tickets have owners.

If you wish to log in as one of the seeded users:
- **Supervisor 1**: `supervisor1` (Password: `password123`)
- **Agent 1**: `agent1` (Password: `password123`)

---

## 🧪 Testing the API

For backend testing, use the provided `backend/api.http` file. It is formatted for use with the VS Code **REST Client** extension. You can execute requests sequentially from top to bottom to run a full smoke test of the application's major workflows.
