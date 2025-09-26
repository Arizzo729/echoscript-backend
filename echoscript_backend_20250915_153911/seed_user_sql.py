import os
import uuid

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

email = "Echoscript.AI@Outlook.com"
password = "SunnySideUp!"

schema = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'free',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
with engine.begin() as conn:
    conn.execute(text(schema))
    conn.execute(
        text(
            "INSERT INTO users (id,email,hashed_password,plan) "
            "VALUES (:id, lower(:email), :hp, 'free') "
            "ON CONFLICT (email) DO NOTHING"
        ),
        {"id": str(uuid.uuid4()), "email": email, "hp": pwd.hash(password)},
    )
print("? Seed complete (or already present).")
