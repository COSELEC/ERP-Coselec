"""Add payment_method to CaisseVoucher String

Revision ID: acf4c2db2683
Revises: 2507dffc443b
Create Date: 2026-08-05 14:08:53.394854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'acf4c2db2683'
down_revision: Union[str, Sequence[str], None] = '2507dffc443b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('caisse_vouchers', sa.Column('payment_method', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('caisse_vouchers', 'payment_method')
