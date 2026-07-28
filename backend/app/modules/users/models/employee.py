from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    matricule = Column(String, unique=True)

    first_name = Column(String)

    last_name = Column(String)

    email = Column(String)

    phone = Column(String)

    position = Column(String)

    status = Column(String)

    department_id = Column(
        Integer,
        ForeignKey("departments.id")
    )
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="employee", cascade="all, delete-orphan")
    project_assignments = relationship("ProjectAssignment", back_populates="employee", cascade="all, delete-orphan")
