"""extend_feedback_and_add_system_logs

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'system_logs' not in existing_tables:
        op.create_table(
            'system_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('level', sa.String(20), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    existing_cols = [col['name'] for col in inspector.get_columns('feedbacks')]

    if 'user_question' not in existing_cols:
        op.add_column('feedbacks', sa.Column('user_question', sa.Text(), nullable=True))
    if 'ai_response' not in existing_cols:
        op.add_column('feedbacks', sa.Column('ai_response', sa.Text(), nullable=True))
    if 'rating' not in existing_cols:
        op.add_column('feedbacks', sa.Column('rating', sa.String(20), nullable=True))
    if 'comment' not in existing_cols:
        op.add_column('feedbacks', sa.Column('comment', sa.Text(), nullable=True))

    op.alter_column('feedbacks', 'full_name', existing_type=sa.String(255), nullable=True)
    op.alter_column('feedbacks', 'email', existing_type=sa.String(255), nullable=True)
    op.alter_column('feedbacks', 'message', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column('feedbacks', 'message', existing_type=sa.Text(), nullable=False)
    op.alter_column('feedbacks', 'email', existing_type=sa.String(255), nullable=False)
    op.alter_column('feedbacks', 'full_name', existing_type=sa.String(255), nullable=False)
    op.drop_column('feedbacks', 'comment')
    op.drop_column('feedbacks', 'rating')
    op.drop_column('feedbacks', 'ai_response')
    op.drop_column('feedbacks', 'user_question')
    op.drop_table('system_logs')
