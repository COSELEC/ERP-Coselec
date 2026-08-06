from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.project.daily_report import DailyReport
from app.modules.daily_reports.domain.ports import IDailyReportRepository, IProjectAssignmentRepository
from app.models.project.assignment import ProjectAssignment


class SqlAlchemyDailyReportRepository(IDailyReportRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_employee_project_week(self, user_id: int, project_id: int, week_start: date) -> Optional[DailyReport]:
        return self.db.query(DailyReport).filter(
            DailyReport.user_id == user_id,
            DailyReport.project_id == project_id,
            DailyReport.week_start == week_start,
        ).first()

    def save(self, report: DailyReport) -> DailyReport:
        self.db.add(report)
        self.db.flush()
        return report

    def find_missing_reports_for_week(self, week_start: date) -> List[dict]:
        """
        Trouve tous les membres ayant une assignment active pendant cette semaine
        qui n'ont pas encore soumis de rapport hebdomadaire.
        """
        query = text("""
            SELECT pa.user_id, pa.project_id
            FROM project_assignments pa
            LEFT JOIN weekly_reports wr
              ON pa.user_id = wr.user_id
              AND pa.project_id = wr.project_id
              AND wr.week_start = :week_start
            WHERE pa.start_date <= :week_start
              AND (pa.end_date IS NULL OR pa.end_date >= :week_start)
              AND wr.id IS NULL
        """)
        result = self.db.execute(query, {"week_start": week_start})
        return [{"user_id": row[0], "project_id": row[1]} for row in result]


class SqlAlchemyProjectAssignmentRepository(IProjectAssignmentRepository):
    def __init__(self, db: Session):
        self.db = db

    def is_active_assignment(self, user_id: int, project_id: int, check_date: date) -> bool:
        assignment = self.db.query(ProjectAssignment).filter(
            ProjectAssignment.user_id == user_id,
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.start_date <= check_date
        ).filter(
            (ProjectAssignment.end_date == None) | (ProjectAssignment.end_date >= check_date)
        ).first()
        return assignment is not None
