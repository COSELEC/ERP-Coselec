from pydantic import BaseModel


from typing import Optional

class EmployeeCreate(BaseModel):
    matricule: str
    first_name: str
    last_name: str

    email: str
    phone: str

    position: str

    status: str

    department_id: int
    manager_id: Optional[int] = None


class EmployeeResponse(EmployeeCreate):
    id: int

    class Config:
        from_attributes = True


class OrgChartNode(BaseModel):
    id: int
    name: str
    position: str
    department: str
    manager_id: Optional[int] = None
    children: list['OrgChartNode'] = []
