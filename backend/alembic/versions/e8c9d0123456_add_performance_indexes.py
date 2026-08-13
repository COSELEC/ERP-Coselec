"""Add performance indexes for high concurrency

Revision ID: e8c9d0123456
Revises: 02a7ba2f576d
Create Date: 2026-08-13 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e8c9d0123456'
down_revision: Union[str, Sequence[str], None] = '02a7ba2f576d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Messages indexing for fast chat loading & history pagination
    op.create_index('ix_messages_room_created', 'messages', ['room_id', 'created_at'], unique=False)
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'], unique=False)

    # Notifications indexing for instantaneous user notification badge lookups
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'], unique=False)

    # Tasks indexing for project Gantt, kanban and filtering
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'], unique=False)
    op.create_index('ix_tasks_assignee_id', 'tasks', ['assignee_id'], unique=False)
    op.create_index('ix_tasks_status', 'tasks', ['status'], unique=False)
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'], unique=False)

    # Requests indexing for SLA, status transitions and user history
    op.create_index('ix_requests_requester_id', 'requests', ['requester_id'], unique=False)
    op.create_index('ix_requests_status_type', 'requests', ['status', 'type'], unique=False)
    op.create_index('ix_requests_project_id', 'requests', ['project_id'], unique=False)

    # Stocks & Stock movements indexing for real-time inventory checks
    op.create_index('ix_stocks_prod_wh_partner', 'stocks', ['product_id', 'warehouse_id', 'partner_id'], unique=False)
    op.create_index('ix_stock_movements_prod_wh', 'stock_movements', ['product_id', 'warehouse_id'], unique=False)
    op.create_index('ix_stock_movements_created_at', 'stock_movements', ['created_at'], unique=False)

    # HR documents indexing
    op.create_index('ix_employee_documents_user_id', 'employee_documents', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_employee_documents_user_id', table_name='employee_documents')
    op.drop_index('ix_stock_movements_created_at', table_name='stock_movements')
    op.drop_index('ix_stock_movements_prod_wh', table_name='stock_movements')
    op.drop_index('ix_stocks_prod_wh_partner', table_name='stocks')
    op.drop_index('ix_requests_project_id', table_name='requests')
    op.drop_index('ix_requests_status_type', table_name='requests')
    op.drop_index('ix_requests_requester_id', table_name='requests')
    op.drop_index('ix_tasks_due_date', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_assignee_id', table_name='tasks')
    op.drop_index('ix_tasks_project_id', table_name='tasks')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_messages_sender_id', table_name='messages')
    op.drop_index('ix_messages_room_created', table_name='messages')
