from app.core.database import engine, Base
# Import all dependent models to populate metadata
from app.modules.users.models.employee import Employee
from app.models.project.project import Project
from app.models.project.daily_report import DailyReport

DailyReport.__table__.create(engine, checkfirst=True)
print("daily_reports table created successfully.")
