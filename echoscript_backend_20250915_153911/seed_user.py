# seed_user.py
import argparse
import os
import uuid

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import Base, User  # reuse models & Base/engine from app.py

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, future=True, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main(email: str, password: str, plan: str = "free"):
    email = email.lower().strip()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == email)).scalars().first()
        if existing:
            print(f"User already exists: {email} (id={existing.id})")
            return
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=pwd_context.hash(password),
            plan=plan,
        )
        db.add(user)
        db.commit()
        print(f"✅ Created user {email} with id={user.id} and plan={user.plan}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--plan", default="free")
    args = p.parse_args()
    main(args.email, args.password, args.plan)
