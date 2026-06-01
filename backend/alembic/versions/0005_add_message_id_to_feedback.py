"""add_message_id_to_feedback

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-23 21:01:38.365047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [col['name'] for col in inspector.get_columns('feedbacks')]
    if 'message_id' not in existing_cols:
        op.add_column('feedbacks', sa.Column('message_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'feedbacks', 'messages', ['message_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint(None, 'feedbacks', type_='foreignkey')
    op.drop_column('feedbacks', 'message_id')
