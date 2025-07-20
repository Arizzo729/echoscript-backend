# signin.py (world-class)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User
from app.auth_utils import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and return an access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # 1. Lookup user by email (OAuth2 uses 'username' field)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Ensure user is active
    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive",
        )

    # 3. Issue JWT
    token_payload = {"sub": str(user.id)}
    access_token = create_access_token(data=token_payload)

    return TokenResponse(access_token=access_token)
