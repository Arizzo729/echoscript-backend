from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Base class for models
Base = declarative_base()

# Define the Transcript table
class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    original_filename = Column(String)
    storage_filename = Column(String)
    content = Column(String)
    duration = Column(Integer)
    file_size = Column(Integer)
    language = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Connect to your SQLite database
DATABASE_URL = "sqlite:///./db.sqlite3"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create the table
Base.metadata.create_all(bind=engine)

print("Transcript table created successfully!")
