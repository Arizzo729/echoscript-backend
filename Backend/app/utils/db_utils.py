from typing import Optional

from sqlalchemy.orm import Session

from app.models import User


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Look up a user by email. Returns None if not found.
    """
    return db.query(User).filter(User.email == email).one_or_none()


def update_user_password(db: Session, email: str, new_hashed_password: str) -> bool:
    """
    Update a user's password. Returns True if the user was found and updated.
    """
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        return False

    user.password = new_hashed_password  # type: ignore[assignment]
    db.commit()
    return True
