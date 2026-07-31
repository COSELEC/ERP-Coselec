from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from app.models.project.daily_report import DailyReport

class IDailyReportRepository(ABC):
    @abstractmethod
    def get_by_employee_project_date(self, employee_id: int, project_id: int, report_date: date) -> Optional[DailyReport]:
        pass

    @abstractmethod
    def save(self, report: DailyReport) -> DailyReport:
        pass

    @abstractmethod
    def find_missing_reports_for_date(self, check_date: date) -> List[dict]:
        """
        Returns a list of dicts with {"employee_id": int, "project_id": int} 
        who have active assignments on check_date but no report.
        """
        pass

class IProjectAssignmentRepository(ABC):
    @abstractmethod
    def is_active_assignment(self, employee_id: int, project_id: int, check_date: date) -> bool:
        pass

class INotificationService(ABC):
    @abstractmethod
    def notify_missing_report(self, employee_id: int, project_id: int):
        pass
