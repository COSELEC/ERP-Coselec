"""Add location fields to PaymentMilestone

Revision ID: f3a9c1d52e87
Revises: 02a7ba2f576d
Create Date: 2026-08-19 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a9c1d52e87'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add region, departement, commune, localite to project_payment_milestones."""
    op.add_column('project_payment_milestones', sa.Column('region',      sa.String(length=100), nullable=True))
    op.add_column('project_payment_milestones', sa.Column('departement', sa.String(length=100), nullable=True))
    op.add_column('project_payment_milestones', sa.Column('commune',     sa.String(length=100), nullable=True))
    op.add_column('project_payment_milestones', sa.Column('localite',    sa.String(length=200), nullable=True))


def downgrade() -> None:
    """Remove location fields from project_payment_milestones."""
    op.drop_column('project_payment_milestones', 'localite')
    op.drop_column('project_payment_milestones', 'commune')
    op.drop_column('project_payment_milestones', 'departement')
    op.drop_column('project_payment_milestones', 'region')
