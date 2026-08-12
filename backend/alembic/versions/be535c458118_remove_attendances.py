"""remove_attendances

Revision ID: be535c458118
Revises: 72820418a087
Create Date: 2026-08-12 09:16:48.410633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be535c458118'
down_revision: Union[str, Sequence[str], None] = '72820418a087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('attendances')


def downgrade() -> None:
    """Downgrade schema."""
    pass
