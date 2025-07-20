# === app/dependencies.py ===

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Generator

from app.models import User
from app.config import Config  # Config is the instantiated config object
from app.db import SessionLocal

# Only enforce strong JWT_SECRET_KEY in production
if not Config.DEBUG and (not Config.JWT_SECRET_KEY or Config.JWT_SECRET_KEY == "supersecret"):
    raise RuntimeError("JWT_SECRET_KEY must be set to a secure value in production")

# Token extractor
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Dependency: Get DB Session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency: Current User
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exc
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Dependency: Admin-Only Routes
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
