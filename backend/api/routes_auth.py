from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.deps import get_current_user
from core.ratelimit import client_ip, login_limiter
from core.security import create_access_token, hash_password, verify_password
from db.database import get_db
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(name=body.name, email=body.email.lower(), password_hash=hash_password(body.password), role="user")
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email}


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    key = f"api|{client_ip(request)}|{body.email.lower()}"
    if login_limiter.blocked(key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts. Try again in a few minutes.")
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash) or not user.is_active:
        login_limiter.fail(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    login_limiter.reset(key)
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "role": user.role}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
