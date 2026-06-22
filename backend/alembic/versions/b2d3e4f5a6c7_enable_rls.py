"""enable row-level security on all app tables

Locks down Supabase's auto-exposed PostgREST API (anon/authenticated roles get
no access, since no policies are defined). The application backend connects as
the table-owner `postgres` role, which bypasses RLS, so app behavior is
unchanged. This clears the "RLS Disabled in Public" critical advisors.

Revision ID: b2d3e4f5a6c7
Revises: a1c2e3f4b5d6
Create Date: 2026-06-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2d3e4f5a6c7'
down_revision: Union[str, None] = 'a1c2e3f4b5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "teams", "users", "audit_log",
    "customers", "interactions",
    "sla_policies", "tickets", "ticket_comments",
    "plans", "addons", "plan_features",
    "subscriptions", "devices",
    "invoices", "payments", "line_items",
    "kb_categories", "kb_articles",
    "alembic_version",
]


def upgrade() -> None:
    # No-op on SQLite (dev/test); only Postgres supports RLS.
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in TABLES:
        op.execute(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY;')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in TABLES:
        op.execute(f'ALTER TABLE public."{t}" DISABLE ROW LEVEL SECURITY;')
