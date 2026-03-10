from app.db import engine
print("Database URL from engine:", engine.url)
print("Dialect:", engine.url.drivername)

# Also check what's in .env
import os
from dotenv import load_dotenv
load_dotenv()
print("\nDATABASE_URL from .env:", os.getenv('DATABASE_URL'))
