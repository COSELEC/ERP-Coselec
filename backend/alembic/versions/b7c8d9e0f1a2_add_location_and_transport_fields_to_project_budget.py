"""Add location and transport fields to project_budgets

Revision ID: b7c8d9e0f1a2
Revises: f3a9c1d52e87
Create Date: 2026-08-19 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'f3a9c1d52e87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_budgets', sa.Column('region',      sa.String(length=100), nullable=True))
    op.add_column('project_budgets', sa.Column('departement', sa.String(length=100), nullable=True))
    op.add_column('project_budgets', sa.Column('commune',     sa.String(length=100), nullable=True))
    op.add_column('project_budgets', sa.Column('localite',    sa.String(length=200), nullable=True))
    op.add_column('project_budgets', sa.Column('quantity',    sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('project_budgets', sa.Column('unit_price',  sa.Numeric(precision=14, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('project_budgets', 'unit_price')
    op.drop_column('project_budgets', 'quantity')
    op.drop_column('project_budgets', 'localite')
    op.drop_column('project_budgets', 'commune')
    op.drop_column('project_budgets', 'departement')
    op.drop_column('project_budgets', 'region')
