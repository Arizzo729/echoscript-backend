import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv("DATABASE_URL")
print("Using DATABASE_URL:", url)

engine = create_engine(url, pool_pre_ping=True)
with engine.connect() as conn:
    print("DB version:", conn.execute(text("select version()")).scalar().split()[0])
    print("Ping:", conn.execute(text("select 1")).scalar())
print("? DB connection OK")
