# === app/utils/safety_check.py ===

import os
import logging
import importlib.util
from app.config import Config

logger = logging.getLogger("echoscript")

# === What we expect to exist ===
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "JWT_SECRET_KEY",
    "DATABASE_URL",
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
    "dotenv",
]


def check_env_vars() -> bool:
    """
    Verify all REQUIRED_ENV_VARS are set.
    Returns True if none are missing; logs and returns False otherwise.
    """
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        logger.critical(f"[ENV ❌] Missing environment variables: {', '.join(missing)}")
        return False
    logger.info("[ENV ✅] All required environment variables are set.")
    return True


def check_directories() -> None:
    """
    Ensure all REQUIRED_DIRS exist, creating them if needed.
    """
    for path in REQUIRED_DIRS:
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                logger.info(f"[DIR 📁] Created missing dir: {path}")
            except Exception as exc:
                logger.warning(f"[DIR ⚠️] Could not create dir {path}: {exc}")
    logger.info("[DIR ✅] All directories verified or created.")


def check_python_packages() -> bool:
    """
    Verify that key Python packages are importable.
    Returns True if all are present; logs and returns False otherwise.
    """
    missing = []
    for pkg in REQUIRED_PACKAGES:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        logger.critical(f"[PKG ❌] Missing required packages: {', '.join(missing)}")
        return False
    logger.info("[PKG ✅] All required packages are installed.")
    return True


def run_safety_checks() -> None:
    """
    Run all startup safety validations.
    Non-fatal failures are logged but do not abort startup.
    """
    logger.info("[Startup Checks] Running safety validation...")

    if not check_env_vars():
        logger.warning("[Startup Checks ⚠️] Continuing despite missing environment variables.")

    check_directories()

    if not check_python_packages():
        logger.warning("[Startup Checks ⚠️] Continuing despite missing Python packages.")

    logger.info("[Startup Checks ✅] Safety validation complete.")

