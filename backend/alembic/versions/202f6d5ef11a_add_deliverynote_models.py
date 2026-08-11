"""Add DeliveryNote models

Revision ID: 202f6d5ef11a
Revises: 2b4c1327f1d0
Create Date: 2026-08-05 15:22:30.578460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '202f6d5ef11a'
down_revision: Union[str, Sequence[str], None] = '2b4c1327f1d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
