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
