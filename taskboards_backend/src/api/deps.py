from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.db import get_db
from src.db.models import User

# OAuth2 scheme for bearer token provided in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# PUBLIC_INTERFACE
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Retrieve the currently authenticated user from a JWT Bearer token.

    Raises:
        HTTPException 401 if token invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user: Optional[User] = db.query(User).filter(User.id == int(sub)).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user
