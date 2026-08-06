from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from app.models.project.daily_report import DailyReport

class IDailyReportRepository(ABC):
    @abstractmethod
    def get_by_employee_project_week(self, user_id: int, project_id: int, week_start: date) -> Optional[DailyReport]:
        """Retourne le rapport de la semaine (identifié par week_start) pour un employé/projet."""
        pass

    @abstractmethod
    def save(self, report: DailyReport) -> DailyReport:
        pass

    @abstractmethod
    def find_missing_reports_for_week(self, week_start: date) -> List[dict]:
        """
        Retourne une liste de dicts {user_id, project_id} dont les membres
        ont une assignment active cette semaine mais n'ont pas encore soumis
        de rapport hebdomadaire.
        """
        pass

class IProjectAssignmentRepository(ABC):
    @abstractmethod
    def is_active_assignment(self, user_id: int, project_id: int, check_date: date) -> bool:
        pass

class INotificationService(ABC):
    @abstractmethod
    def notify_missing_report(self, user_id: int, project_id: int):
        pass
