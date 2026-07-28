from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    matricule: str
    first_name: str
    last_name: str

    email: str
    phone: str

    position: str

    status: str

    department_id: int


class EmployeeResponse(EmployeeCreate):
    id: int

    class Config:
        from_attributes = True
