import logging
from datetime import date
from app.core.database import SessionLocal
from app.modules.daily_reports.adapters.sqlalchemy_repo import SqlAlchemyDailyReportRepository
from app.modules.daily_reports.adapters.notification_adapter import WebSocketNotificationAdapter
from app.modules.daily_reports.domain.use_cases import CheckAndNotifyMissingReportsUseCase

logger = logging.getLogger(__name__)

def check_missing_daily_reports():
    logger.info("Starting check for missing daily reports...")
    try:
        db = SessionLocal()
        report_repo = SqlAlchemyDailyReportRepository(db)
        notification_service = WebSocketNotificationAdapter(db)
        
        use_case = CheckAndNotifyMissingReportsUseCase(report_repo, notification_service)
        
        # Check for today
        use_case.execute(date.today())
        
        # The WebSocketNotificationAdapter performs db.add() and db.flush(), 
        # so we should commit after use_case execution.
        db.commit()
        logger.info("Finished check for missing daily reports.")
    except Exception as e:
        logger.error(f"Error checking missing daily reports: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
