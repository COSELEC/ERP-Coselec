"""Initial migration

Revision ID: 2507dffc443b
Revises: 
Create Date: 2026-08-05 12:51:12.611902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2507dffc443b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_table('chatrooms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('is_group', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatrooms_id'), 'chatrooms', ['id'], unique=False)
    op.create_table('clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('contact_name', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('address', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_code'), 'clients', ['code'], unique=True)
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)
    op.create_table('departments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.create_table('norm_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_norm_categories_id'), 'norm_categories', ['id'], unique=False)
    op.create_index(op.f('ix_norm_categories_name'), 'norm_categories', ['name'], unique=False)
    op.create_table('partners',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_partners_id'), 'partners', ['id'], unique=False)
    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('quality_kpi_processus',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_kpi_processus_id'), 'quality_kpi_processus', ['id'], unique=False)
    op.create_index(op.f('ix_quality_kpi_processus_name'), 'quality_kpi_processus', ['name'], unique=True)
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_table('warehouses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_warehouses_id'), 'warehouses', ['id'], unique=False)
    op.create_table('norms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['norm_categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_norms_code'), 'norms', ['code'], unique=True)
    op.create_index(op.f('ix_norms_id'), 'norms', ['id'], unique=False)
    op.create_index(op.f('ix_norms_title'), 'norms', ['title'], unique=False)
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('designation', sa.String(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(), nullable=True),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('unit_price', sa.Integer(), nullable=True),
    sa.Column('minimum_stock', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_table('quality_kpi_indicators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('processus_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['processus_id'], ['quality_kpi_processus.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_kpi_indicators_id'), 'quality_kpi_indicators', ['id'], unique=False)
    op.create_table('role_permissions',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.Column('requires_password_change', sa.Boolean(), nullable=True),
    sa.Column('matricule', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('position', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('manager_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('matricule')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('target_user_id', sa.Integer(), nullable=True),
    sa.Column('action_type', sa.String(), nullable=True),
    sa.Column('old_value', sa.String(), nullable=True),
    sa.Column('new_value', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action_type'), 'audit_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_table('chatroom_members',
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['chatrooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('room_id', 'user_id')
    )
    op.create_table('contracts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('contract_type', sa.String(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_id'), 'contracts', ['id'], unique=False)
    op.create_table('employee_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.Enum('IDENTITY', 'SOCIAL', 'CONTRACT', name='documentcategory'), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('storage_path', sa.String(), nullable=False),
    sa.Column('mime_type', sa.String(), nullable=True),
    sa.Column('numero', sa.String(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employee_documents_id'), 'employee_documents', ['id'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('file_url', sa.String(), nullable=True),
    sa.Column('file_name', sa.String(), nullable=True),
    sa.Column('file_type', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['chatrooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_table('norm_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('norm_id', sa.Integer(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('file_url', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['norm_id'], ['norms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_norm_versions_id'), 'norm_versions', ['id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('nom', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('STUDY', 'PLANNED', 'APPROVED', 'ONGOING', 'SUSPENDED', 'DELAYED', 'BLOCKED', 'VALIDATION', 'FINISHED', 'CLOSED', 'CANCELED', name='projectstatus'), nullable=False),
    sa.Column('project_type', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_archived', sa.Boolean(), nullable=True),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('chef_projet_id', sa.Integer(), nullable=True),
    sa.Column('date_debut_estimee', sa.Date(), nullable=False),
    sa.Column('date_debut_reelle', sa.Date(), nullable=True),
    sa.Column('date_fin_estimee', sa.Date(), nullable=False),
    sa.Column('date_fin_prevue', sa.Date(), nullable=False),
    sa.Column('date_fin_reelle', sa.Date(), nullable=True),
    sa.Column('budget_estime', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('budget_engage', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['chef_projet_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('quality_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('IN_REVIEW', 'APPROVED', 'REJECTED', 'PUBLISHED', name='qualitydocstatus'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_documents_id'), 'quality_documents', ['id'], unique=False)
    op.create_table('quality_kpi_values',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('indicator_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('value_raw', sa.String(length=100), nullable=True),
    sa.Column('value_numeric', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['indicator_id'], ['quality_kpi_indicators.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('indicator_id', 'year', 'month', name='uix_kpi_value_indicator_year_month')
    )
    op.create_index(op.f('ix_quality_kpi_values_id'), 'quality_kpi_values', ['id'], unique=False)
    op.create_table('quality_kpi_yearly_targets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('indicator_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('frequency', sa.String(length=50), nullable=True),
    sa.Column('target_raw', sa.String(length=100), nullable=True),
    sa.Column('target_numeric', sa.Float(), nullable=True),
    sa.Column('target_numeric_max', sa.Float(), nullable=True),
    sa.Column('operator', sa.Enum('GTE', 'LTE', 'BETWEEN', 'EQ', name='kpioperator'), nullable=True),
    sa.ForeignKeyConstraint(['indicator_id'], ['quality_kpi_indicators.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('indicator_id', 'year', name='uix_kpi_target_indicator_year')
    )
    op.create_index(op.f('ix_quality_kpi_yearly_targets_id'), 'quality_kpi_yearly_targets', ['id'], unique=False)
    op.create_table('user_roles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_table('attendances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('notes', sa.String(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendances_id'), 'attendances', ['id'], unique=False)
    op.create_table('daily_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('report_date', sa.Date(), nullable=False),
    sa.Column('hours_worked', sa.Float(), nullable=False),
    sa.Column('progress_percentage', sa.Integer(), nullable=True),
    sa.Column('tasks_completed', sa.Text(), nullable=False),
    sa.Column('issues_encountered', sa.Text(), nullable=True),
    sa.Column('plan_for_tomorrow', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'APPROVED', name='reportstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'project_id', 'report_date', name='uq_employee_project_date')
    )
    op.create_index(op.f('ix_daily_reports_id'), 'daily_reports', ['id'], unique=False)
    op.create_table('project_assignments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=False),
    sa.Column('allocation', sa.Float(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_assignments_id'), 'project_assignments', ['id'], unique=False)
    op.create_table('project_budgets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('allocated_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_budgets_id'), 'project_budgets', ['id'], unique=False)
    op.create_table('project_partners',
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('project_id', 'partner_id')
    )
    op.create_table('project_phases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=True),
    sa.Column('date_debut', sa.Date(), nullable=True),
    sa.Column('date_fin', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', name='phasestatus'), nullable=True),
    sa.Column('completion_percent', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_phases_id'), 'project_phases', ['id'], unique=False)
    op.create_table('purchase_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('requester_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='purchaserequeststatus'), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('expected_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_requests_id'), 'purchase_requests', ['id'], unique=False)
    op.create_table('quality_document_role_reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('assigned_user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='reviewstatus'), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['quality_documents.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_document_role_reviews_id'), 'quality_document_role_reviews', ['id'], unique=False)
    op.create_table('quality_document_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('r2_file_key', sa.String(), nullable=False),
    sa.Column('original_filename', sa.String(), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['quality_documents.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_document_versions_id'), 'quality_document_versions', ['id'], unique=False)
    op.create_table('quality_document_visible_roles',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['quality_documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id', 'role_id')
    )
    op.create_table('stock_movements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('warehouse_id', sa.Integer(), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('ENTRY', 'EXIT', 'TRANSFER_IN', 'TRANSFER_OUT', 'ADJUSTMENT', 'ENTRY_GENERAL', 'ENTRY_PROJECT', 'TRANSFER_TO_PROJECT', 'PROJECT_CONSUMPTION', name='movementtype'), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_movements_id'), 'stock_movements', ['id'], unique=False)
    op.create_table('stocks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('warehouse_id', sa.Integer(), nullable=False),
    sa.Column('partner_id', sa.Integer(), nullable=True),
    sa.Column('stock_type', sa.Enum('GENERAL', 'PROJECT', name='stocktype'), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stocks_id'), 'stocks', ['id'], unique=False)
    op.create_table('project_milestones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('phase_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('achieved_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'ACHIEVED', 'DELAYED', name='milestonestatus'), nullable=True),
    sa.ForeignKeyConstraint(['phase_id'], ['project_phases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_milestones_id'), 'project_milestones', ['id'], unique=False)
    op.create_table('requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('LEAVE', 'IT_EQUIPMENT', 'IT_ACCESS', 'IT_INCIDENT', 'FACILITY_MAINTENANCE', 'FACILITY_BADGE', 'FACILITY_SUPPLIES', 'FUEL', 'DOCUMENT', 'OTHER', name='requesttype'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'PENDING_MANAGER_APPROVAL', 'PENDING_FINANCE_APPROVAL', 'APPROVED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'REJECTED', name='requeststatus'), nullable=True),
    sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='requestpriority'), nullable=True),
    sa.Column('requester_id', sa.Integer(), nullable=False),
    sa.Column('validator_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('rejection_comment', sa.String(), nullable=True),
    sa.Column('payload', sa.JSON(), nullable=True),
    sa.Column('attachment_url', sa.String(), nullable=True),
    sa.Column('sla_deadline', sa.DateTime(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('manager_validator_id', sa.Integer(), nullable=True),
    sa.Column('manager_validated_at', sa.DateTime(), nullable=True),
    sa.Column('finance_validator_id', sa.Integer(), nullable=True),
    sa.Column('finance_validated_at', sa.DateTime(), nullable=True),
    sa.Column('linked_product_id', sa.Integer(), nullable=True),
    sa.Column('linked_purchase_request_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['finance_validator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['linked_product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['linked_purchase_request_id'], ['purchase_requests.id'], ),
    sa.ForeignKeyConstraint(['manager_validator_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['validator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requests_id'), 'requests', ['id'], unique=False)
    op.create_table('purchase_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('purchase_request_id', sa.Integer(), nullable=True),
    sa.Column('generic_request_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('supplier_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'ISSUED', 'APPROVED', 'DELIVERED', 'CANCELLED', name='purchaseorderstatus'), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('pdf_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['generic_request_id'], ['requests.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['purchase_request_id'], ['purchase_requests.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['supplier_id'], ['partners.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_orders_id'), 'purchase_orders', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_reference'), 'purchase_orders', ['reference'], unique=True)
    op.create_table('request_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('old_status', sa.String(), nullable=True),
    sa.Column('new_status', sa.String(), nullable=False),
    sa.Column('changed_by_id', sa.Integer(), nullable=False),
    sa.Column('comment', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_history_id'), 'request_history', ['id'], unique=False)
    op.create_index(op.f('ix_request_history_request_id'), 'request_history', ['request_id'], unique=False)
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE', 'ARCHIVED', name='taskstatus'), nullable=False),
    sa.Column('priority', sa.Enum('URGENT', 'HIGH', 'MEDIUM', 'LOW', name='taskpriority'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('assignee_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('milestone_id', sa.Integer(), nullable=True),
    sa.Column('task_metadata', sa.JSON(), nullable=True),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['milestone_id'], ['project_milestones.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_stock_reservations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('reserved_by_id', sa.Integer(), nullable=True),
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'CONSUMED', 'CANCELLED', name='reservationstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('consumed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reserved_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_stock_reservations_id'), 'project_stock_reservations', ['id'], unique=False)
    op.create_table('purchase_order_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('purchase_order_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('budget_id', sa.Integer(), nullable=True),
    sa.Column('designation', sa.String(length=255), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['budget_id'], ['project_budgets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_order_lines_id'), 'purchase_order_lines', ['id'], unique=False)
    op.create_table('reception_controls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('po_id', sa.Integer(), nullable=True),
    sa.Column('supplier_id', sa.Integer(), nullable=True),
    sa.Column('delivery_date', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('pdf_url', sa.String(), nullable=True),
    sa.Column('stock_type', sa.String(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['partners.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reception_controls_id'), 'reception_controls', ['id'], unique=False)
    op.create_table('task_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('storage_path', sa.String(), nullable=False),
    sa.Column('mime_type', sa.String(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_expenses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('budget_id', sa.Integer(), nullable=True),
    sa.Column('purchase_order_line_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('date_incurred', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='expensestatus'), nullable=True),
    sa.Column('proof_document_url', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['budget_id'], ['project_budgets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['purchase_order_line_id'], ['purchase_order_lines.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_expenses_id'), 'project_expenses', ['id'], unique=False)
    op.create_table('reception_control_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reception_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('designation', sa.String(), nullable=False),
    sa.Column('qty_ordered', sa.Integer(), nullable=True),
    sa.Column('qty_delivered', sa.Integer(), nullable=True),
    sa.Column('is_compliant', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['reception_id'], ['reception_controls.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reception_control_lines_id'), 'reception_control_lines', ['id'], unique=False)
    op.create_table('bank_vouchers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_name', sa.String(length=100), nullable=False),
    sa.Column('check_number', sa.String(length=50), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('period_num', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('recipient', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'FINALIZED', 'VOID', name='voucherstatus'), nullable=True),
    sa.Column('finalized_at', sa.DateTime(), nullable=True),
    sa.Column('amount_in_numbers', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('amount_in_letters', sa.String(length=500), nullable=False),
    sa.Column('pdf_url', sa.String(length=500), nullable=True),
    sa.Column('linked_caisse_voucher_ids', sa.JSON(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('expense_id', sa.Integer(), nullable=True),
    sa.Column('reservation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['expense_id'], ['project_expenses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reservation_id'], ['project_stock_reservations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('check_number')
    )
    op.create_index(op.f('ix_bank_vouchers_id'), 'bank_vouchers', ['id'], unique=False)
    op.create_table('caisse_vouchers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('num', sa.String(length=50), nullable=True),
    sa.Column('affaire', sa.String(length=255), nullable=True),
    sa.Column('cia', sa.String(length=255), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'FINALIZED', 'VOID', name='voucherstatus'), nullable=True),
    sa.Column('finalized_at', sa.DateTime(), nullable=True),
    sa.Column('pdf_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('expense_id', sa.Integer(), nullable=True),
    sa.Column('reservation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['expense_id'], ['project_expenses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reservation_id'], ['project_stock_reservations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_caisse_vouchers_id'), 'caisse_vouchers', ['id'], unique=False)
    op.create_table('analytical_allocations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_voucher_id', sa.Integer(), nullable=False),
    sa.Column('cost_center_code', sa.String(length=50), nullable=False),
    sa.Column('cost_center_name', sa.String(length=255), nullable=False),
    sa.Column('client', sa.String(length=255), nullable=True),
    sa.Column('analytical_account', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['bank_voucher_id'], ['bank_vouchers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytical_allocations_id'), 'analytical_allocations', ['id'], unique=False)
    op.create_table('caisse_voucher_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('voucher_id', sa.Integer(), nullable=False),
    sa.Column('line_type', sa.Enum('EXPENSE', 'RECEIPT', name='caissevoucherlinetype'), nullable=False),
    sa.Column('date', sa.String(length=50), nullable=True),
    sa.Column('designation', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['voucher_id'], ['caisse_vouchers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_caisse_voucher_lines_id'), 'caisse_voucher_lines', ['id'], unique=False)
    op.create_table('voucher_attachments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_voucher_id', sa.Integer(), nullable=True),
    sa.Column('caisse_voucher_id', sa.Integer(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('storage_path', sa.String(length=500), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bank_voucher_id'], ['bank_vouchers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['caisse_voucher_id'], ['caisse_vouchers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voucher_attachments_id'), 'voucher_attachments', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_voucher_attachments_id'), table_name='voucher_attachments')
    op.drop_table('voucher_attachments')
    op.drop_index(op.f('ix_caisse_voucher_lines_id'), table_name='caisse_voucher_lines')
    op.drop_table('caisse_voucher_lines')
    op.drop_index(op.f('ix_analytical_allocations_id'), table_name='analytical_allocations')
    op.drop_table('analytical_allocations')
    op.drop_index(op.f('ix_caisse_vouchers_id'), table_name='caisse_vouchers')
    op.drop_table('caisse_vouchers')
    op.drop_index(op.f('ix_bank_vouchers_id'), table_name='bank_vouchers')
    op.drop_table('bank_vouchers')
    op.drop_index(op.f('ix_reception_control_lines_id'), table_name='reception_control_lines')
    op.drop_table('reception_control_lines')
    op.drop_index(op.f('ix_project_expenses_id'), table_name='project_expenses')
    op.drop_table('project_expenses')
    op.drop_table('task_documents')
    op.drop_index(op.f('ix_reception_controls_id'), table_name='reception_controls')
    op.drop_table('reception_controls')
    op.drop_index(op.f('ix_purchase_order_lines_id'), table_name='purchase_order_lines')
    op.drop_table('purchase_order_lines')
    op.drop_index(op.f('ix_project_stock_reservations_id'), table_name='project_stock_reservations')
    op.drop_table('project_stock_reservations')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_request_history_request_id'), table_name='request_history')
    op.drop_index(op.f('ix_request_history_id'), table_name='request_history')
    op.drop_table('request_history')
    op.drop_index(op.f('ix_purchase_orders_reference'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')
    op.drop_index(op.f('ix_requests_id'), table_name='requests')
    op.drop_table('requests')
    op.drop_index(op.f('ix_project_milestones_id'), table_name='project_milestones')
    op.drop_table('project_milestones')
    op.drop_index(op.f('ix_stocks_id'), table_name='stocks')
    op.drop_table('stocks')
    op.drop_index(op.f('ix_stock_movements_id'), table_name='stock_movements')
    op.drop_table('stock_movements')
    op.drop_table('quality_document_visible_roles')
    op.drop_index(op.f('ix_quality_document_versions_id'), table_name='quality_document_versions')
    op.drop_table('quality_document_versions')
    op.drop_index(op.f('ix_quality_document_role_reviews_id'), table_name='quality_document_role_reviews')
    op.drop_table('quality_document_role_reviews')
    op.drop_index(op.f('ix_purchase_requests_id'), table_name='purchase_requests')
    op.drop_table('purchase_requests')
    op.drop_index(op.f('ix_project_phases_id'), table_name='project_phases')
    op.drop_table('project_phases')
    op.drop_table('project_partners')
    op.drop_index(op.f('ix_project_budgets_id'), table_name='project_budgets')
    op.drop_table('project_budgets')
    op.drop_index(op.f('ix_project_assignments_id'), table_name='project_assignments')
    op.drop_table('project_assignments')
    op.drop_index(op.f('ix_daily_reports_id'), table_name='daily_reports')
    op.drop_table('daily_reports')
    op.drop_index(op.f('ix_attendances_id'), table_name='attendances')
    op.drop_table('attendances')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_quality_kpi_yearly_targets_id'), table_name='quality_kpi_yearly_targets')
    op.drop_table('quality_kpi_yearly_targets')
    op.drop_index(op.f('ix_quality_kpi_values_id'), table_name='quality_kpi_values')
    op.drop_table('quality_kpi_values')
    op.drop_index(op.f('ix_quality_documents_id'), table_name='quality_documents')
    op.drop_table('quality_documents')
    op.drop_table('projects')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_norm_versions_id'), table_name='norm_versions')
    op.drop_table('norm_versions')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_employee_documents_id'), table_name='employee_documents')
    op.drop_table('employee_documents')
    op.drop_index(op.f('ix_contracts_id'), table_name='contracts')
    op.drop_table('contracts')
    op.drop_table('chatroom_members')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action_type'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_quality_kpi_indicators_id'), table_name='quality_kpi_indicators')
    op.drop_table('quality_kpi_indicators')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_norms_title'), table_name='norms')
    op.drop_index(op.f('ix_norms_id'), table_name='norms')
    op.drop_index(op.f('ix_norms_code'), table_name='norms')
    op.drop_table('norms')
    op.drop_index(op.f('ix_warehouses_id'), table_name='warehouses')
    op.drop_table('warehouses')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_quality_kpi_processus_name'), table_name='quality_kpi_processus')
    op.drop_index(op.f('ix_quality_kpi_processus_id'), table_name='quality_kpi_processus')
    op.drop_table('quality_kpi_processus')
    op.drop_table('permissions')
    op.drop_index(op.f('ix_partners_id'), table_name='partners')
    op.drop_table('partners')
    op.drop_index(op.f('ix_norm_categories_name'), table_name='norm_categories')
    op.drop_index(op.f('ix_norm_categories_id'), table_name='norm_categories')
    op.drop_table('norm_categories')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_table('departments')
    op.drop_index(op.f('ix_clients_id'), table_name='clients')
    op.drop_index(op.f('ix_clients_code'), table_name='clients')
    op.drop_table('clients')
    op.drop_index(op.f('ix_chatrooms_id'), table_name='chatrooms')
    op.drop_table('chatrooms')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
