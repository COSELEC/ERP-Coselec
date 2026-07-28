from sqlalchemy import Column, Integer, ForeignKey, Table
from app.core.database import Base

task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("dependency_id", Integer, ForeignKey("tasks.id"), primary_key=True),
)
