"""Add signature_url to User

Revision ID: 2b4c1327f1d0
Revises: acf4c2db2683
Create Date: 2026-08-05 15:18:21.078153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b4c1327f1d0'
down_revision: Union[str, Sequence[str], None] = 'acf4c2db2683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('signature_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'signature_url')
