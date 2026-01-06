# app/routes/verify_email.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import VerifyEmailRequest, VerifyEmailResponse

router = APIRouter(prefix="/verify-email", tags=["Verify Email"])


@router.post("/", response_model=VerifyEmailResponse)
def verify_email(
    payload: VerifyEmailRequest, db: Session = Depends(get_db)
) -> VerifyEmailResponse:
    user: User | None = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_verified = True  # type: ignore[assignment]
    db.commit()
    return VerifyEmailResponse(verified=True)
