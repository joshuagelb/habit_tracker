from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app import schemas, crud
from app.deps import get_db
from app.security import create_access_token, verify_password

router = APIRouter()

@router.post('/register', response_model=schemas.UserRead)
def register(user: schemas.UserCreate, session: Session = Depends(get_db)):
    from app.crud import get_user_by_email, create_user
    existing = get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    u = create_user(session, user.email, user.password)
    return u

@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, session: Session = Depends(get_db)):
    from app.crud import get_user_by_email
    user = get_user_by_email(session, form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}
