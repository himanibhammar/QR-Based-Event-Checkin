from pydantic import BaseModel
from datetime import datetime

class EventCreateSchema(BaseModel):
    name: str
    date: datetime
    location: str
    description: str

    class Config:
        orm_mode = True
