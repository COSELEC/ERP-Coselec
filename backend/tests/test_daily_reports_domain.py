import pytest
from datetime import date
from typing import List, Optional
from app.models.project.daily_report import DailyReport, ReportStatus
from app.modules.daily_reports.domain.ports import IDailyReportRepository, IProjectAssignmentRepository, INotificationService
from app.modules.daily_reports.domain.use_cases import SubmitDailyReportUseCase, CheckAndNotifyMissingReportsUseCase
from app.modules.daily_reports.domain.exceptions import NotAssignedException, DuplicateReportException
from unittest.mock import patch

class DummyDailyReport:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)



class MockDailyReportRepository(IDailyReportRepository):
    def __init__(self):
        self.reports = []
        self.missing_reports_mock_data = []

    def get_by_employee_project_date(self, employee_id: int, project_id: int, report_date: date) -> Optional[DailyReport]:
        for r in self.reports:
            if r.employee_id == employee_id and r.project_id == project_id and r.report_date == report_date:
                return r
        return None

    def save(self, report: DailyReport) -> DailyReport:
        self.reports.append(report)
        return report

    def find_missing_reports_for_date(self, check_date: date) -> List[dict]:
        return self.missing_reports_mock_data

class MockProjectAssignmentRepository(IProjectAssignmentRepository):
    def __init__(self):
        self.active_assignments = set() 

    def is_active_assignment(self, employee_id: int, project_id: int, check_date: date) -> bool:
        return (employee_id, project_id, check_date) in self.active_assignments

class MockNotificationService(INotificationService):
    def __init__(self):
        self.notifications_sent = []

    def notify_missing_report(self, employee_id: int, project_id: int):
        self.notifications_sent.append((employee_id, project_id))


def test_cannot_submit_if_no_active_assignment():
    report_repo = MockDailyReportRepository()
    assignment_repo = MockProjectAssignmentRepository()
    use_case = SubmitDailyReportUseCase(report_repo, assignment_repo)

    with pytest.raises(NotAssignedException):
        use_case.execute(
            employee_id=1, project_id=10, report_date=date(2026, 7, 30),
            hours_worked=8, progress_percentage=50,
            tasks_completed="Task A", issues_encountered="", plan_for_tomorrow=""
        )

@patch('app.modules.daily_reports.domain.use_cases.DailyReport', DummyDailyReport)
def test_cannot_submit_duplicate_report_same_day():
    report_repo = MockDailyReportRepository()
    assignment_repo = MockProjectAssignmentRepository()
    
    employee_id, project_id, d = 1, 10, date(2026, 7, 30)
    assignment_repo.active_assignments.add((employee_id, project_id, d))
    
    use_case = SubmitDailyReportUseCase(report_repo, assignment_repo)

    use_case.execute(
        employee_id, project_id, d, 8, 50, "Task A", "", ""
    )

    with pytest.raises(DuplicateReportException):
        use_case.execute(
            employee_id, project_id, d, 8, 50, "Task B", "", ""
        )

@patch('app.modules.daily_reports.domain.use_cases.DailyReport', DummyDailyReport)
def test_success_report_submission():
    report_repo = MockDailyReportRepository()
    assignment_repo = MockProjectAssignmentRepository()
    
    employee_id, project_id, d = 1, 10, date(2026, 7, 30)
    assignment_repo.active_assignments.add((employee_id, project_id, d))
    
    use_case = SubmitDailyReportUseCase(report_repo, assignment_repo)

    report = use_case.execute(
        employee_id, project_id, d, 8.5, 60, "Task A", "None", "Task C"
    )

    assert report.employee_id == 1
    assert report.project_id == 10
    assert report.hours_worked == 8.5
    assert report.status.value == "SUBMITTED"
    assert len(report_repo.reports) == 1

def test_missing_reports_identification():
    report_repo = MockDailyReportRepository()
    notification_service = MockNotificationService()
    
    report_repo.missing_reports_mock_data = [
        {"employee_id": 1, "project_id": 10},
        {"employee_id": 2, "project_id": 10},
    ]

    use_case = CheckAndNotifyMissingReportsUseCase(report_repo, notification_service)
    use_case.execute(date(2026, 7, 30))

    assert len(notification_service.notifications_sent) == 2
    assert (1, 10) in notification_service.notifications_sent
    assert (2, 10) in notification_service.notifications_sent
