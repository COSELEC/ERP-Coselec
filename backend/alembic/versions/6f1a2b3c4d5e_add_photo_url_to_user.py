"""Add photo_url to User

Revision ID: 6f1a2b3c4d5e
Revises: 5e90dce47cb3
Create Date: 2026-09-08 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6f1a2b3c4d5e'
down_revision: Union[str, Sequence[str], None] = '5e90dce47cb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('photo_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'photo_url')
