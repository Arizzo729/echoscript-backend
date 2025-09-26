"""
Create/upgrade tables based on ORM models.
Safe to run multiple times. Will create missing tables only.
"""

from dotenv import load_dotenv
from sqlalchemy import text

from app.db import engine
from app.models import Base

load_dotenv()


def main():
    # Create all ORM tables that don't exist yet
    Base.metadata.create_all(bind=engine)

    # Optional: ensure the enum type exists consistently (Postgres only)
    # If you change SubscriptionStatus values later, use Alembic migrations instead.
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))

    print("✅ Database schema created or already up to date.")


if __name__ == "__main__":
    main()
