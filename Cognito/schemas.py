from pydantic import BaseModel, EmailStr

class SignUpSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
