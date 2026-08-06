from pydantic import BaseModel


from typing import Optional

class EmployeeCreate(BaseModel):
    matricule: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    supervised_employee_ids: Optional[list[int]] = None


class EmployeeResponse(EmployeeCreate):
    id: int

    class Config:
        from_attributes = True


class OrgChartNode(BaseModel):
    id: int
    name: str
    position: str
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    matricule: Optional[str] = None
    status: Optional[str] = None
    manager_id: Optional[int] = None
    children: list['OrgChartNode'] = []
