from datetime import date
from app.models.project.daily_report import DailyReport, ReportStatus
from app.modules.daily_reports.domain.ports import IDailyReportRepository, IProjectAssignmentRepository, INotificationService
from app.modules.daily_reports.domain.exceptions import NotAssignedException, DuplicateReportException

class SubmitDailyReportUseCase:
    def __init__(self, report_repo: IDailyReportRepository, assignment_repo: IProjectAssignmentRepository):
        self.report_repo = report_repo
        self.assignment_repo = assignment_repo

    def execute(self, employee_id: int, project_id: int, report_date: date, hours_worked: float, 
                progress_percentage: int, tasks_completed: str, issues_encountered: str, plan_for_tomorrow: str) -> DailyReport:
        
        # Rule 1: Must have an active assignment for this project on this date
        if not self.assignment_repo.is_active_assignment(employee_id, project_id, report_date):
            raise NotAssignedException()

        # Rule 2: Cannot submit two reports for the same project on the same day
        existing_report = self.report_repo.get_by_employee_project_date(employee_id, project_id, report_date)
        if existing_report:
            raise DuplicateReportException()

        new_report = DailyReport(
            employee_id=employee_id,
            project_id=project_id,
            report_date=report_date,
            hours_worked=hours_worked,
            progress_percentage=progress_percentage,
            tasks_completed=tasks_completed,
            issues_encountered=issues_encountered,
            plan_for_tomorrow=plan_for_tomorrow,
            status=ReportStatus.SUBMITTED
        )

        return self.report_repo.save(new_report)

class CheckAndNotifyMissingReportsUseCase:
    def __init__(self, report_repo: IDailyReportRepository, notification_service: INotificationService):
        self.report_repo = report_repo
        self.notification_service = notification_service

    def execute(self, check_date: date):
        missing = self.report_repo.find_missing_reports_for_date(check_date)
        for item in missing:
            self.notification_service.notify_missing_report(item["employee_id"], item["project_id"])
