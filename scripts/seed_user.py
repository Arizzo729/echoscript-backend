# scripts/seed_user.py
from __future__ import annotations

import argparse

from passlib.context import CryptContext
from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main(email: str, password: str) -> None:
    email = email.lower().strip()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == email)).scalars().first()
        if existing:
            print(f"User already exists: {email} (id={existing.id})")
            return
        user = User(email=email, password=pwd.hash(password), is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created user {email} with id={user.id}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    args = p.parse_args()
    main(args.email, args.password)
