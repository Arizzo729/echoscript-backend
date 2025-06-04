# ---- EchoScript.AI: config.py ----

import os
import redis
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ---- Application ----
    APP_NAME = "EchoScript.AI"
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

    # ---- API Keys ----
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # HuggingFace

    # ---- JWT Auth ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # ---- Redis / DB ----
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

    # ---- Paths ----
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
    STORAGE_DIR = os.path.join(BASE_DIR, "transcripts")
    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    # ---- File Uploads ----
    ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "mp4"}

# ---- Ensure Required Folders Exist ----
for folder in [Config.UPLOAD_FOLDER, Config.STORAGE_DIR, Config.EXPORT_DIR, Config.LOG_DIR]:
    os.makedirs(folder, exist_ok=True)

# ---- Redis Client ----
try:
    redis_client = redis.Redis.from_url(Config.REDIS_URL)
    redis_client.ping()  # optional connection check
except Exception as e:
    redis_client = None
    print(f"[Redis Warning] Could not connect: {e}")

