from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.relations import user_roles
from app.modules.users.models.department import Department

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    requires_password_change = Column(Boolean, default=False)

    matricule = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    position = Column(String, nullable=True)
    status = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signature_url = Column(String, nullable=True)

    department = relationship("Department")
    manager = relationship("User", remote_side=[id], back_populates="subordinates")
    subordinates = relationship("User", back_populates="manager")
    
    documents = relationship("EmployeeDocument", back_populates="user", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="user", cascade="all, delete-orphan")
    project_assignments = relationship("ProjectAssignment", back_populates="user", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")

    notifications = relationship(
        "Notification",
        back_populates="user"
    )
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    @property
    def supervised_employee_ids(self) -> list[int]:
        if self.subordinates:
            return [sub.id for sub in self.subordinates]
        return []

