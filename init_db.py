from sqlalchemy import create_engine
from app.models import Base  # adjust to your project

engine = create_engine("sqlite:///./db.sqlite3", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
