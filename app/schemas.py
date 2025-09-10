from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_per_day: int = 1

class HabitRead(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    target_per_day: int
    created_at: datetime

    class Config:
        orm_mode = True

class CheckInCreate(BaseModel):
    date: Optional[date] = None
    count: int = 1

class CheckInRead(BaseModel):
    id: int
    habit_id: int
    date: date
    count: int

    class Config:
        orm_mode = True
