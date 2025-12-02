from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.core.security import create_access_token, get_password_hash, verify_password
from src.db import get_db
from src.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str = Field(..., description="JWT bearer token")
    token_type: str = Field("bearer", description="Token type")


class RegisterIn(BaseModel):
    email: EmailStr = Field(..., description="Email")
    name: str | None = Field(None, description="Display name")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")


class LoginIn(BaseModel):
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=8, description="Password")


@router.post("/register", summary="Register a new user", response_model=TokenOut, status_code=201)
def register_user(payload: RegisterIn, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user account.

    Args:
        payload: email, name, password

    Returns:
        JWT access token for the newly created user.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", summary="Login and get JWT", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> Any:
    """
    Authenticate a user and return a JWT.

    Args:
        payload: email and password

    Returns:
        JWT access token.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}
