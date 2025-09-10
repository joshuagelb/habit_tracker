from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "changeme-please-set-env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DATABASE_URL: str = "sqlite:///./habit_tracker.db"

    class Config:
        env_file = ".env"

settings = Settings()
