"""replace daily_reports with weekly_reports

Revision ID: 72820418a087
Revises: d13b7859cf30
Create Date: 2026-08-06 11:05:56.937578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '72820418a087'
down_revision: Union[str, Sequence[str], None] = 'd13b7859cf30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remplace la table daily_reports par weekly_reports.
    Le type ENUM reportstatus existe déjà en DB — on le réutilise via SQL brut.
    """
    # Créer la nouvelle table avec SQL brut pour éviter toute tentative de CREATE TYPE
    op.execute("""
        CREATE TABLE weekly_reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            week_start DATE NOT NULL,
            week_end DATE NOT NULL,
            report_date DATE NOT NULL,
            hours_worked DOUBLE PRECISION NOT NULL,
            progress_percentage INTEGER,
            tasks_completed TEXT NOT NULL,
            issues_encountered TEXT,
            plan_next_week TEXT,
            status reportstatus DEFAULT 'SUBMITTED',
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            CONSTRAINT uq_employee_project_week UNIQUE (user_id, project_id, week_start)
        )
    """)
    op.create_index('ix_weekly_reports_id', 'weekly_reports', ['id'], unique=False)

    # Supprimer l'ancienne table
    op.drop_index('ix_daily_reports_id', table_name='daily_reports')
    op.drop_table('daily_reports')
    # Le type ENUM reportstatus est conservé (toujours utilisé par weekly_reports)


def downgrade() -> None:
    """Restaure la table daily_reports."""
    op.execute("""
        CREATE TABLE daily_reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            report_date DATE NOT NULL,
            hours_worked DOUBLE PRECISION NOT NULL,
            progress_percentage INTEGER,
            tasks_completed TEXT NOT NULL,
            issues_encountered TEXT,
            plan_for_tomorrow TEXT,
            status reportstatus DEFAULT 'SUBMITTED',
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            CONSTRAINT uq_employee_project_date UNIQUE (user_id, project_id, report_date)
        )
    """)
    op.create_index('ix_daily_reports_id', 'daily_reports', ['id'], unique=False)
    op.drop_index('ix_weekly_reports_id', table_name='weekly_reports')
    op.drop_table('weekly_reports')
