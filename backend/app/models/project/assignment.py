from sqlalchemy import Column, Integer, String, Date, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import date

class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(String(100), nullable=False)
    allocation = Column(Float, nullable=False, default=100.0) # 0 to 100 percentage
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="assignments")
    user = relationship("User", back_populates="project_assignments")

    @property
    def current_status(self) -> str:
        today = date.today()
        if today < self.start_date:
            return "Upcoming"
        elif self.end_date and today > self.end_date:
            return "Completed"
        else:
            return "Active"
