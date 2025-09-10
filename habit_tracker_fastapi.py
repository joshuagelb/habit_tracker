# Habit Tracker FastAPI - Project Skeleton

This repository contains a complete FastAPI backend for a Habit Tracker application.

---

# File: README.md
"""
# Habit Tracker API (FastAPI)

A lightweight, production-ready FastAPI backend for tracking habits, daily check-ins, and streaks.

## Features
- User registration & JWT authentication
- CRUD for Habits
- Daily check-ins for habits
- Streak calculation and weekly/monthly statistics endpoints
- SQLite for quick start (can swap to Postgres)
- Dockerfile and GitHub Actions CI template
- Tests with pytest and httpx AsyncClient

## Tech Stack
- FastAPI
- SQLModel (built on SQLAlchemy)
- SQLite (dev) / Postgres (prod)
- python-jose for JWT
- passlib for password hashing
- Uvicorn for ASGI server

## Quick start (local)
```bash
# create virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run migrations (if using SQLModel simple create)
python -m app.db.create_db

# start
uvicorn app.main:app --reload
```

## Docker
```bash
docker build -t habit-tracker-api .
docker run -p 8000:8000 habit-tracker-api
```

## API Overview
- POST /auth/register -> register
- POST /auth/login -> get access token
- GET /habits -> list user's habits
- POST /habits -> create habit
- GET /habits/{id} -> get habit
- PUT /habits/{id} -> update habit
- DELETE /habits/{id} -> delete habit
- POST /habits/{id}/checkin -> mark a habit done for a date
- GET /habits/{id}/streak -> current streak
- GET /stats/weekly -> weekly summary

"""

---

# File: requirements.txt
"""
fastapi==0.99.2
uvicorn[standard]==0.23.2
sqlmodel==0.0.8
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.24.1
pytest==7.4.0
pytest-asyncio==0.22.0
alembic==1.11.1
python-multipart==0.0.6
"""

---

# File: app/__init__.py
"""
# package marker
"""

---

# File: app/config.py
"""
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "changeme-please-set-env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DATABASE_URL: str = "sqlite:///./habit_tracker.db"

    class Config:
        env_file = ".env"

settings = Settings()
"""

---

# File: app/db/create_db.py
"""
# simple db creator for sqlite (dev use)
from app.db.session import engine
from app import models

if __name__ == '__main__':
    print("Creating database tables...")
    models.SQLModel.metadata.create_all(bind=engine)
    print("Done.")
"""

---

# File: app/db/session.py
"""
from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

def get_session():
    with Session(engine) as session:
        yield session
"""

---

# File: app/models.py
"""
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
"""

---

# File: app/schemas.py
"""
from typing import Optional, List
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
"""

---

# File: app/security.py
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed: str) -> bool:
    return pwd_context.verify(plain_password, hashed)

def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=(expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
"""

---

# File: app/crud.py
"""
from sqlmodel import Session, select
from app import models
from app.security import hash_password, verify_password
from typing import Optional
from datetime import date, datetime, timedelta

# User operations
def get_user_by_email(session: Session, email: str) -> Optional[models.User]:
    return session.exec(select(models.User).where(models.User.email == email)).first()

def create_user(session: Session, email: str, password: str) -> models.User:
    hashed = hash_password(password)
    user = models.User(email=email, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Habit ops
def create_habit(session: Session, owner_id: int, name: str, description: str | None, target_per_day: int) -> models.Habit:
    habit = models.Habit(owner_id=owner_id, name=name, description=description, target_per_day=target_per_day)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit

def get_habits_for_user(session: Session, owner_id: int):
    return session.exec(select(models.Habit).where(models.Habit.owner_id == owner_id)).all()

def get_habit(session: Session, habit_id: int, owner_id: int) -> Optional[models.Habit]:
    return session.exec(select(models.Habit).where(models.Habit.id == habit_id, models.Habit.owner_id == owner_id)).first()

def delete_habit(session: Session, habit: models.Habit):
    session.delete(habit)
    session.commit()

# Check-in ops
def checkin(session: Session, habit: models.Habit, checkin_date: date, count: int = 1):
    # ensure only one checkin row per date — increment if exists
    existing = session.exec(select(models.CheckIn).where(models.CheckIn.habit_id == habit.id, models.CheckIn.date == checkin_date)).first()
    if existing:
        existing.count += count
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    ci = models.CheckIn(habit_id=habit.id, date=checkin_date, count=count)
    session.add(ci)
    session.commit()
    session.refresh(ci)
    return ci

def get_checkins(session: Session, habit_id: int):
    return session.exec(select(models.CheckIn).where(models.CheckIn.habit_id == habit_id).order_by(models.CheckIn.date)).all()

# Streak calculation
def calculate_streak(session: Session, habit_id: int, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    checkins = get_checkins(session, habit_id)
    dates = {c.date for c in checkins}
    streak = 0
    cur = as_of
    while True:
        if cur in dates:
            streak += 1
            cur = cur - timedelta(days=1)
        else:
            break
    return streak

# Weekly stats (simple example)
def weekly_summary(session: Session, owner_id: int, week_start: date):
    # returns count of checkins per habit in 7-day window
    week_end = week_start + timedelta(days=6)
    habits = get_habits_for_user(session, owner_id)
    result = []
    for h in habits:
        cnt = session.exec(select(models.CheckIn).where(models.CheckIn.habit_id == h.id, models.CheckIn.date >= week_start, models.CheckIn.date <= week_end)).all()
        total = sum(c.count for c in cnt)
        result.append({"habit_id": h.id, "name": h.name, "total_checkins": total})
    return result
"""

---

# File: app/deps.py
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.security import decode_access_token
from app.db.session import get_session
from sqlmodel import Session
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    yield from get_session()

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db)) -> models.User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user_id = payload.get("sub")
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
"""

---

# File: app/main.py
"""
from fastapi import FastAPI
from app.routers import auth, habits, stats

app = FastAPI(title="Habit Tracker API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(habits.router, prefix="/habits", tags=["habits"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

@app.get('/')
def read_root():
    return {"msg": "Habit Tracker API. Visit /docs for OpenAPI UI."}
"""

---

# File: app/routers/auth.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app import schemas, crud, models
from app.deps import get_db
from app.security import create_access_token, verify_password

router = APIRouter()

@router.post('/register', response_model=schemas.UserRead)
def register(user: schemas.UserCreate, session: Session = Depends(get_db)):
    existing = crud.get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    u = crud.create_user(session, user.email, user.password)
    return u

@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, session: Session = Depends(get_db)):
    user = crud.get_user_by_email(session, form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}
"""

---

# File: app/routers/habits.py
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app import schemas, crud, models
from app.deps import get_current_user, get_db
from datetime import date

router = APIRouter()

@router.post('/', response_model=schemas.HabitRead)
def create_habit(h: schemas.HabitCreate, session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_habit(session, current_user.id, h.name, h.description, h.target_per_day)

@router.get('/', response_model=List[schemas.HabitRead])
def list_habits(session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_habits_for_user(session, current_user.id)

@router.get('/{habit_id}', response_model=schemas.HabitRead)
def get_habit(habit_id: int, session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = crud.get_habit(session, habit_id, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail='Not found')
    return habit

@router.delete('/{habit_id}')
def delete_habit(habit_id: int, session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = crud.get_habit(session, habit_id, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail='Not found')
    crud.delete_habit(session, habit)
    return {"ok": True}

@router.post('/{habit_id}/checkin', response_model=schemas.CheckInRead)
def checkin(habit_id: int, payload: schemas.CheckInCreate, session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = crud.get_habit(session, habit_id, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail='Not found')
    checkin_date = payload.date or date.today()
    ci = crud.checkin(session, habit, checkin_date, payload.count)
    return ci

@router.get('/{habit_id}/streak')
def get_streak(habit_id: int, session: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = crud.get_habit(session, habit_id, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail='Not found')
    s = crud.calculate_streak(session, habit_id)
    return {"streak": s}
"""

---

# File: app/routers/stats.py
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.deps import get_current_user, get_db
from app import crud, models
from datetime import date, datetime

router = APIRouter()

@router.get('/weekly')
def weekly(current_user: models.User = Depends(get_current_user), session: Session = Depends(get_db)):
    # default to current week's Monday
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return crud.weekly_summary(session, current_user.id, start)
"""

---

# File: Dockerfile
"""
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PORT=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

---

# File: .github/workflows/python-app.yml
"""
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
"""

---

# File: tests/test_basic.py
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.db.session import engine
from app.models import SQLModel

@pytest.fixture(autouse=True)
def create_db():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    yield
    SQLModel.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        r = await ac.post('/auth/register', json={'email': 'a@b.com', 'password': 'pass'})
        assert r.status_code == 200
        r = await ac.post('/auth/login', json={'email': 'a@b.com', 'password': 'pass'})
        assert r.status_code == 200
        token = r.json()['access_token']
        assert token

@pytest.mark.asyncio
async def test_habit_crud_and_checkin():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        await ac.post('/auth/register', json={'email': 'u@u.com', 'password': 'pwd'})
        r = await ac.post('/auth/login', json={'email': 'u@u.com', 'password': 'pwd'})
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        # create
        r = await ac.post('/habits/', json={'name': 'Run', 'description': 'Run 5k'}, headers=headers)
        assert r.status_code == 200
        hid = r.json()['id']
        # checkin
        r = await ac.post(f'/habits/{hid}/checkin', json={}, headers=headers)
        assert r.status_code == 200
        # streak
        r = await ac.get(f'/habits/{hid}/streak', headers=headers)
        assert r.status_code == 200
        assert r.json()['streak'] >= 1
"""

---

# Notes
"""
This skeleton is intentionally opinionated but minimal to help you iterate quickly.
Next steps I can implement for you on request:
- Add pagination, filtering, and full-text search for habits
- Add Alembic migrations and Postgres setup
- Add an example React frontend (Next.js) that uses the API
- Add refresh tokens + token revocation
- Improve tests coverage and linting

Tell me which of the above you'd like next and I will implement it.
"""
