import sys
from pathlib import Path

# Ensure current directory is in sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import Base, engine  # your SQLAlchemy Base and engine

# Create tables
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully")
