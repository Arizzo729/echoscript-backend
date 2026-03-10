"""
Seed or ensure a user exists using explicit ORM models (no reflection).
Keeps your existing DB column name 'password' to match your current table.

Usage:
    python scripts/create_user.py "you@example.com" "Passw0rd!23"
"""

import argparse
import sys
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import User

# bcrypt pin recommended on Windows: bcrypt==4.0.1, passlib==1.7.4
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plaintext: str) -> str:
    return pwd_context.hash(plaintext)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("password")
    args = parser.parse_args()

    email = args.email.strip().lower()
    plaintext = args.password

    with SessionLocal() as db:  # type: Session
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"ℹ️  User already exists: {email}")
            return

        user = User(
            email=email,
            password=hash_password(plaintext),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            print(f"ERROR creating user: {e}", file=sys.stderr)
            raise

        print(f"✅ Created user: {email}")


if __name__ == "__main__":
    main()
