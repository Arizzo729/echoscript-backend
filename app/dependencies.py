from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import config  # centralized settings
from app.db import get_db
from app.models import User

# OAuth2 scheme expecting the frontend to call /api/auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the JWT token using config.JWT_SECRET_KEY and returns the associated User.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use the secret and algorithm from centralized config  [^1]
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exc from None
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        # JWTError covers signature/expiration issues; ValueError/TypeError for int conversion
        raise credentials_exc from None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures the current user has admin privileges.
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
