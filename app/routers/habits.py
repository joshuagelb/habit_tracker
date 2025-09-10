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
