from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

def get_session():
    with Session(engine) as session:
        yield session
