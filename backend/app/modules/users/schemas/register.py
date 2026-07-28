from pydantic import BaseModel, EmailStr



class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str

    class Config:
        from_attributes = True
