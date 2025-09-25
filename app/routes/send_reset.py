# app/routes/send_reset.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.routes.password_reset import request_reset
from app.schemas.auth import PasswordResetRequest, PasswordResetResponse

router = APIRouter(prefix="/api/auth", tags=["Password Reset (legacy)"])


@router.post(
    "/send-reset", response_model=PasswordResetResponse, summary="Legacy reset alias"
)
def send_reset(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    return request_reset(payload, db=db)
