# app/database.py

from sqlalchemy.orm import Session
from app.models import User
from app.db import get_db


def get_user_by_email(email: str) -> User | None:
    db: Session = next(get_db())
    return db.query(User).filter(User.email == email).first()


def update_user_password(email: str, new_hashed_password: str) -> bool:
    db: Session = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False

    user.password = new_hashed_password
    db.commit()
    db.refresh(user)
    return True
