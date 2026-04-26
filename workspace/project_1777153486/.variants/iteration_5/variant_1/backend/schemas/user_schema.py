from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    
class UserRegister(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str