from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.deps import get_current_user, get_db
from app import crud, models
from datetime import date, timedelta

router = APIRouter()

@router.get('/weekly')
def weekly(current_user: models.User = Depends(get_current_user), session: Session = Depends(get_db)):
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return crud.weekly_summary(session, current_user.id, start)
