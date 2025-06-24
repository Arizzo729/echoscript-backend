# === app/database.py — User DB Utils ===

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import User
from app.db import get_db
import logging

logger = logging.getLogger("echoscript")

def get_user_by_email(email: str) -> User | None:
    db_gen = get_db()
    db: Session = next(db_gen, None)
    if not db:
        logger.warning("Failed to acquire DB session")
        return None

    try:
        return db.query(User).filter(User.email == email).first()
    except SQLAlchemyError as e:
        logger.exception(f"[DB ERROR] get_user_by_email failed: {e}")
        return None
    finally:
        db.close()

def update_user_password(email: str, new_hashed_password: str) -> bool:
    db_gen = get_db()
    db: Session = next(db_gen, None)
    if not db:
        logger.warning("Failed to acquire DB session")
        return False

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False

        user.password = new_hashed_password
        db.commit()
        db.refresh(user)
        return True
    except SQLAlchemyError as e:
        logger.exception(f"[DB ERROR] update_user_password failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()