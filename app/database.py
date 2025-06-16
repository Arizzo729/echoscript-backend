# app/database.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import User
from app.db import get_db


def get_user_by_email(email: str) -> User | None:
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        user = db.query(User).filter(User.email == email).first()
        return user
    except StopIteration:
        return None
    except SQLAlchemyError as e:
        print(f"[DB ERROR] get_user_by_email: {e}")
        return None


def update_user_password(email: str, new_hashed_password: str) -> bool:
    try:
        db_gen = get_db()
        db: Session = next(db_gen)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False

        user.password = new_hashed_password
        db.commit()
        db.refresh(user)
        return True
    except StopIteration:
        return False
    except SQLAlchemyError as e:
        print(f"[DB ERROR] update_user_password: {e}")
        return False
