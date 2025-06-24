from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr

from app.db import get_db
from app.models import User
from app.auth_utils import hash_password
from app.utils.logger import logger
from app.config import redis_client

router = APIRouter(prefix="/auth", tags=["Authentication"])


class VerifyReset(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=10)
    new_password: constr(min_length=8, max_length=64)


@router.post("/verify-reset")
def verify_reset(data: VerifyReset, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host

    key = f"reset:{data.email}"
    stored_code = redis_client.get(key)
    if not stored_code:
        logger.warning(f"[Reset] Expired or invalid code for {data.email} from IP {ip}")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Reset code expired or invalid.")

    if stored_code.decode() != data.code:
        logger.warning(f"[Reset] Incorrect reset code attempt for {data.email} from IP {ip}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset code.")

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        logger.warning(f"[Reset] User not found during reset: {data.email} from IP {ip}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    redis_client.delete(key)

    logger.info(f"[Reset] ✅ Password successfully reset for {data.email} from IP {ip}")
    return {"status": "success", "message": "Your password has been reset successfully."}


