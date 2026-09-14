"""Add PIECE_CAISSE to requesttype enum

Revision ID: 72bcf84bad43
Revises: 7c5ca2ea3cdb
Create Date: 2026-09-14 10:47:50.702222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72bcf84bad43'
down_revision: Union[str, Sequence[str], None] = '7c5ca2ea3cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE requesttype ADD VALUE IF NOT EXISTS 'PIECE_CAISSE'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL does not support dropping a value from an enum type easily.
    pass
