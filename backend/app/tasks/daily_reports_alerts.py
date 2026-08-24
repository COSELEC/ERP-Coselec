import logging
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.modules.daily_reports.adapters.sqlalchemy_repo import SqlAlchemyDailyReportRepository
from app.modules.daily_reports.adapters.notification_adapter import WebSocketNotificationAdapter
from app.modules.daily_reports.domain.use_cases import CheckAndNotifyMissingReportsUseCase

logger = logging.getLogger(__name__)


def check_missing_daily_reports():
    """
    Vérifie les rapports hebdomadaires manquants.
    Déclenché le vendredi à 16h via APScheduler.
    Notifie les chefs d'équipe/projet qui n'ont pas encore soumis
    leur rapport pour la semaine en cours.
    """
    today = date.today()
    monday_of_week = today - timedelta(days=today.weekday())

    print(f"Vérification des rapports hebdomadaires manquants pour la semaine du {monday_of_week}...")
    try:
        db = SessionLocal()
        report_repo = SqlAlchemyDailyReportRepository(db)
        notification_service = WebSocketNotificationAdapter(db)

        use_case = CheckAndNotifyMissingReportsUseCase(report_repo, notification_service)
        use_case.execute(today)

        db.commit()
        print("Vérification des rapports hebdomadaires terminée.")
    except Exception as e:
        print(f"Erreur lors de la vérification des rapports hebdomadaires: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
