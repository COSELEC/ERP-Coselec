"""add_compromise_pending_to_request_status

Revision ID: b300c84a7a33
Revises: be535c458118
Create Date: 2026-08-12 10:49:04.911763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b300c84a7a33'
down_revision: Union[str, Sequence[str], None] = 'be535c458118'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE requeststatus ADD VALUE IF NOT EXISTS 'COMPROMISE_PENDING'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
