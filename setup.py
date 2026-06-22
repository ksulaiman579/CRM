"""
Scaffolding helper for the Telecom Customer-Service CRM (backend tree).

Creates the backend directory/file skeleton described in plan.md (Phase 0.1).
The frontend is scaffolded separately with `create-next-app` (see plan.md Phase 0.4).

Run from the repo root:  python setup.py
Safe to re-run: it never overwrites existing files.
"""
import os

# Repo root = directory containing this script.
base = os.path.dirname(os.path.abspath(__file__))

dirs = [
    "backend/alembic/versions",
    "backend/app/db",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/api/v1",
    "backend/app/services",
    "backend/tests",
]

files = [
    "backend/.env.example",
    "backend/requirements.txt",
    "backend/api.http",
    "backend/alembic.ini",
    "backend/tests/conftest.py",
    "backend/tests/test_auth_bootstrap.py",
    "backend/tests/test_ticket_lifecycle.py",
    "backend/app/__init__.py",
    "backend/app/main.py",
    "backend/app/config.py",
    "backend/app/db/__init__.py",
    "backend/app/db/base.py",
    "backend/app/db/session.py",
    "backend/app/db/seed.py",
    "backend/app/core/__init__.py",
    "backend/app/core/security.py",
    "backend/app/core/deps.py",
    "backend/app/core/errors.py",
    "backend/app/core/sla.py",
    "backend/app/models/__init__.py",
    "backend/app/models/user.py",
    "backend/app/models/customer.py",
    "backend/app/models/service.py",
    "backend/app/models/billing.py",
    "backend/app/models/plan.py",
    "backend/app/models/ticket.py",
    "backend/app/models/kb.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/__init__.py",
    "backend/app/api/router.py",
    "backend/app/api/v1/__init__.py",
    "backend/app/api/v1/auth.py",
    "backend/app/api/v1/users.py",
    "backend/app/api/v1/customers.py",
    "backend/app/api/v1/tickets.py",
    "backend/app/api/v1/interactions.py",
    "backend/app/api/v1/billing.py",
    "backend/app/api/v1/plans.py",
    "backend/app/api/v1/kb.py",
    "backend/app/api/v1/dashboard.py",
    "backend/app/services/__init__.py",
    "backend/app/services/ticket_service.py",
    "backend/app/services/customer_service.py",
    "backend/app/services/dashboard_service.py",
    "docker-compose.yml",
    ".gitignore",
    "README.md",
    "run.ps1",
    "run.bat",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

for f in files:
    path = os.path.join(base, f)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "a").close()

print("Backend skeleton created. Next: scaffold the frontend (see plan.md Phase 0.4).")
