"""Add attendances table

Revision ID: c7a8b9e01234
Revises: e8c9d0123456
Create Date: 2026-08-18 13:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7a8b9e01234'
down_revision: Union[str, Sequence[str], None] = 'e8c9d0123456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('check_in', sa.DateTime(), nullable=True),
        sa.Column('check_out', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendances_id'), 'attendances', ['id'], unique=False)
    op.create_index(op.f('ix_attendances_user_id'), 'attendances', ['user_id'], unique=False)
    op.create_index(op.f('ix_attendances_date'), 'attendances', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_attendances_date'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_user_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_id'), table_name='attendances')
    op.drop_table('attendances')
