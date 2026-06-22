"""team.code + agent presence status

Revision ID: c3e4f5a6b7d8
Revises: b2d3e4f5a6c7
Create Date: 2026-06-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3e4f5a6b7d8'
down_revision: Union[str, None] = 'b2d3e4f5a6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teams', sa.Column('code', sa.Text(), nullable=True))
    op.create_unique_constraint('uq_teams_code', 'teams', ['code'])
    op.add_column('users', sa.Column('status', sa.Text(), nullable=False, server_default='offline'))
    op.add_column('users', sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'status_changed_at')
    op.drop_column('users', 'status')
    op.drop_constraint('uq_teams_code', 'teams', type_='unique')
    op.drop_column('teams', 'code')
