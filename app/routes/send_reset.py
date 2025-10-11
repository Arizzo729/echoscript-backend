# app/routes/send_reset.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.routes.password_reset import request_reset
from app.schemas.auth import PasswordResetRequest, PasswordResetResponse

router = APIRouter(prefix="/auth", tags=["Password Reset"])

@router.post("/send-reset-code", response_model=PasswordResetResponse, summary="Send password reset email")
def send_reset_code(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> PasswordResetResponse:
    return request_reset(payload, db=db)
