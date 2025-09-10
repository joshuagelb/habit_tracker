from typing import Optional, List
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    habits: List["Habit"] = Relationship(back_populates="owner")

class Habit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    target_per_day: int = Field(default=1, description="How many times per day target")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner: Optional[User] = Relationship(back_populates="habits")
    checkins: List["CheckIn"] = Relationship(back_populates="habit")

class CheckIn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id")
    date: date
    count: int = Field(default=1)

    habit: Optional[Habit] = Relationship(back_populates="checkins")
