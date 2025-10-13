# app/models/create_user.py

import argparse
import sys
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import User
from app.utils.auth_utils import hash_password

def main():
    parser = argparse.ArgumentParser(description="Create a new user in the database.")
    parser.add_argument("email", help="The email address of the user.")
    parser.add_argument("password", help="The password for the user.")
    parser.add_argument("--admin", action="store_true", help="Flag to create the user as an admin.")
    args = parser.parse_args()

    email = args.email.strip().lower()
    plaintext_password = args.password

    with SessionLocal() as db:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: User with email '{email}' already exists.", file=sys.stderr)
            return

        new_user = User(
            email=email,
            password=hash_password(plaintext_password),
            is_active=True,
            is_verified=True,  # Users created via CLI are considered verified
            is_admin=args.admin,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            db.add(new_user)
            db.commit()
            print(f"Successfully created user: {email}")
            if args.admin:
                print("User has been granted admin privileges.")
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()