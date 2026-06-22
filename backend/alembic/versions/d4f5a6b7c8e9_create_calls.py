"""create calls table (contact-center ACD)

Revision ID: d4f5a6b7c8e9
Revises: c3e4f5a6b7d8
Create Date: 2026-06-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4f5a6b7c8e9'
down_revision: Union[str, None] = 'c3e4f5a6b7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'calls',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('call_number', sa.Text(), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('intent', sa.Text(), nullable=False),
        sa.Column('opening_line', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='queued'),
        sa.Column('assigned_agent_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_calls_call_number', 'calls', ['call_number'], unique=True)
    op.create_index('ix_calls_customer_id', 'calls', ['customer_id'])
    op.create_index('ix_calls_team_id', 'calls', ['team_id'])
    op.create_index('ix_calls_status', 'calls', ['status'])
    op.create_index('ix_calls_assigned_agent_id', 'calls', ['assigned_agent_id'])
    # Match the RLS posture of every other table (PostgREST anon locked out).
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute('ALTER TABLE public."calls" ENABLE ROW LEVEL SECURITY;')


def downgrade() -> None:
    op.drop_table('calls')
