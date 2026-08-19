"""Merge heads before adding location fields

Revision ID: a1b2c3d4e5f6
Revises: c7a8b9e01234, 02a7ba2f576d
Create Date: 2026-08-19 10:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = ('c7a8b9e01234', '02a7ba2f576d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
