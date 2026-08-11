"""add check_in check_out to attendances

Revision ID: d13b7859cf30
Revises: 202f6d5ef11a
Create Date: 2026-08-06 10:54:10.200979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd13b7859cf30'
down_revision: Union[str, Sequence[str], None] = '202f6d5ef11a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('delivery_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(), nullable=True),
    sa.Column('purchase_order_id', sa.Integer(), nullable=True),
    sa.Column('supplier_name', sa.String(), nullable=True),
    sa.Column('supplier_reference', sa.String(), nullable=True),
    sa.Column('delivery_date', sa.DateTime(), nullable=True),
    sa.Column('storekeeper_id', sa.Integer(), nullable=True),
    sa.Column('storekeeper_validated_at', sa.DateTime(), nullable=True),
    sa.Column('project_manager_id', sa.Integer(), nullable=True),
    sa.Column('project_manager_validated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_manager_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ),
    sa.ForeignKeyConstraint(['storekeeper_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delivery_notes_id'), 'delivery_notes', ['id'], unique=False)
    op.create_index(op.f('ix_delivery_notes_reference'), 'delivery_notes', ['reference'], unique=True)
    op.create_table('delivery_note_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('delivery_note_id', sa.Integer(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('designation', sa.String(), nullable=False),
    sa.Column('ordered_quantity', sa.Float(), nullable=True),
    sa.Column('delivered_quantity', sa.Float(), nullable=True),
    sa.Column('is_compliant', sa.Boolean(), nullable=True),
    sa.Column('remarks', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delivery_note_lines_id'), 'delivery_note_lines', ['id'], unique=False)
    op.add_column('attendances', sa.Column('check_in', sa.DateTime(), nullable=True))
    op.add_column('attendances', sa.Column('check_out', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('attendances', 'check_out')
    op.drop_column('attendances', 'check_in')
    op.drop_index(op.f('ix_delivery_note_lines_id'), table_name='delivery_note_lines')
    op.drop_table('delivery_note_lines')
    op.drop_index(op.f('ix_delivery_notes_reference'), table_name='delivery_notes')
    op.drop_index(op.f('ix_delivery_notes_id'), table_name='delivery_notes')
    op.drop_table('delivery_notes')
