# app/utils/safety_check.py

import os
import sys
import shutil
import logging
import importlib.util
from app.config import Config

logger = logging.getLogger("echoscript")

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "JWT_SECRET_KEY",
    "DATABASE_URL"
]

REQUIRED_DIRS = [
    Config.UPLOAD_FOLDER,
    Config.STORAGE_DIR,
    Config.EXPORT_DIR,
    Config.LOG_DIR,
]

REQUIRED_PACKAGES = [
    "torch",
    "fastapi",
    "redis",
    "sqlalchemy",
    "uvicorn",
    "dotenv"
]

def check_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        logger.critical(f"[ENV ❌] Missing environment variables: {', '.join(missing)}")
        raise EnvironmentError(f"Missing env vars: {missing}")
    logger.info("[ENV ✅] All required environment variables found.")

def check_directories():
    for path in REQUIRED_DIRS:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"[DIR 📁] Created missing dir: {path}")
    logger.info("[DIR ✅] All directories verified.")

def check_python_packages():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        logger.critical(f"[PKG ❌] Missing required packages: {', '.join(missing)}")
        raise ModuleNotFoundError(f"Missing required packages: {missing}")
    logger.info("[PKG ✅] All required packages are installed.")

def run_safety_checks():
    logger.info("[Startup Checks] Running safety validation...")
    check_env_vars()
    check_directories()
    check_python_packages()
    logger.info("[Startup Checks ✅] All safety checks passed.")
