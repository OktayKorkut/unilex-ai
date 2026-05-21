"""add_user_profile_and_session_title

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('history_saved', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('users', sa.Column('anonymized', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('avatar_url', sa.String(512), nullable=True))
    op.add_column('chat_sessions', sa.Column('title', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'history_saved')
    op.drop_column('users', 'anonymized')
    op.drop_column('users', 'avatar_url')
    op.drop_column('chat_sessions', 'title')
