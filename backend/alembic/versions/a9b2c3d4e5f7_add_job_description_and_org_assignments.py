"""Add job_description to users and create org_assignments table

Revision ID: a9b2c3d4e5f7
Revises: 5e90dce47cb3
Create Date: 2026-09-11 11:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a9b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = ('6f1a2b3c4d5e', '5e90dce47cb3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add job_description column to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_description', sa.String(), nullable=True))

    # Create org_assignments table
    op.create_table(
        'org_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('position_key', sa.String(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_org_assignments_id'), 'org_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_org_assignments_position_key'), 'org_assignments', ['position_key'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_org_assignments_position_key'), table_name='org_assignments')
    op.drop_index(op.f('ix_org_assignments_id'), table_name='org_assignments')
    op.drop_table('org_assignments')
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('job_description')
