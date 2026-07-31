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

    def get_by_employee_project_date(self, employee_id: int, project_id: int, report_date: date) -> Optional[DailyReport]:
        return self.db.query(DailyReport).filter(
            DailyReport.employee_id == employee_id,
            DailyReport.project_id == project_id,
            DailyReport.report_date == report_date
        ).first()

    def save(self, report: DailyReport) -> DailyReport:
        self.db.add(report)
        self.db.flush()
        return report

    def find_missing_reports_for_date(self, check_date: date) -> List[dict]:
        # Fetch all active assignments for the check_date that DO NOT have a corresponding daily report
        query = text("""
            SELECT pa.employee_id, pa.project_id 
            FROM project_assignments pa
            LEFT JOIN daily_reports dr 
              ON pa.employee_id = dr.employee_id 
              AND pa.project_id = dr.project_id 
              AND dr.report_date = :check_date
            WHERE pa.start_date <= :check_date 
              AND (pa.end_date IS NULL OR pa.end_date >= :check_date)
              AND dr.id IS NULL
        """)
        
        result = self.db.execute(query, {"check_date": check_date})
        return [{"employee_id": row[0], "project_id": row[1]} for row in result]

class SqlAlchemyProjectAssignmentRepository(IProjectAssignmentRepository):
    def __init__(self, db: Session):
        self.db = db

    def is_active_assignment(self, employee_id: int, project_id: int, check_date: date) -> bool:
        assignment = self.db.query(ProjectAssignment).filter(
            ProjectAssignment.employee_id == employee_id,
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.start_date <= check_date
        ).filter(
            (ProjectAssignment.end_date == None) | (ProjectAssignment.end_date >= check_date)
        ).first()
        return assignment is not None
