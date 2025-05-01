from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRegisterSchema(BaseModel):
    name: str
    email: EmailStr
    student_id: str
    password: str
class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str



class EventRegistration(BaseModel):
    event_id: str

# class EventCreateSchema(BaseModel):
#     name: str
#     date: datetime
#     location: str
#     description: str

#     class Config:
#         orm_mode = True