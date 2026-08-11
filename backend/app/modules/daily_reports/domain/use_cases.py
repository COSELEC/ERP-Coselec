from datetime import date, timedelta
from app.models.project.daily_report import DailyReport, ReportStatus
from app.modules.daily_reports.domain.ports import IDailyReportRepository, IProjectAssignmentRepository, INotificationService
from app.modules.daily_reports.domain.exceptions import NotAssignedException, DuplicateReportException


def _week_bounds(ref_date: date):
    """Calcule le lundi et vendredi de la semaine contenant ref_date."""
    monday = ref_date - timedelta(days=ref_date.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


class SubmitDailyReportUseCase:
    """Use-case de soumission d'un rapport hebdomadaire d'avancement."""

    def __init__(self, report_repo: IDailyReportRepository, assignment_repo: IProjectAssignmentRepository):
        self.report_repo = report_repo
        self.assignment_repo = assignment_repo

    def execute(
        self,
        user_id: int,
        project_id: int,
        report_date: date,
        week_start: date,
        week_end: date,
        hours_worked: float,
        progress_percentage: int,
        tasks_completed: str,
        issues_encountered: str,
        plan_next_week: str,
    ) -> DailyReport:

        if not self.assignment_repo.is_active_assignment(user_id, project_id, report_date):
            raise NotAssignedException()

        existing = self.report_repo.get_by_employee_project_week(user_id, project_id, week_start)
        if existing:
            raise DuplicateReportException()

        new_report = DailyReport(
            user_id=user_id,
            project_id=project_id,
            week_start=week_start,
            week_end=week_end,
            report_date=report_date,
            hours_worked=hours_worked,
            progress_percentage=progress_percentage,
            tasks_completed=tasks_completed,
            issues_encountered=issues_encountered,
            plan_next_week=plan_next_week,
            status=ReportStatus.SUBMITTED,
        )

        return self.report_repo.save(new_report)


class CheckAndNotifyMissingReportsUseCase:
    """Vérifie les rapports manquants pour la semaine et notifie les membres."""

    def __init__(self, report_repo: IDailyReportRepository, notification_service: INotificationService):
        self.report_repo = report_repo
        self.notification_service = notification_service

    def execute(self, check_date: date):
        monday, _ = _week_bounds(check_date)
        missing = self.report_repo.find_missing_reports_for_week(monday)
        for item in missing:
            self.notification_service.notify_missing_report(item["user_id"], item["project_id"])
