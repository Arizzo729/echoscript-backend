import logging
import os

from app.config import config

logger = logging.getLogger("echoscript")

REQUIRED_ENV_VARS: list[str] = [
    "DATABASE_URL",
    "REDIS_URL",
    "OPENAI_API_KEY",
    "HF_TOKEN",
    "STRIPE_SECRET_KEY",
    "JWT_SECRET_KEY",
]

REQUIRED_DIRS: list[str] = [
    config.STORAGE_DIR,
    config.EXPORT_DIR,
    config.LOG_DIR,
    config.UPLOAD_FOLDER,
]


def run_safety_checks() -> None:
    """
    Run startup checks to verify environment and filesystem are properly configured.
    Logs warnings or errors for missing configuration.
    """
    # Check environment variables
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value:
            logger.warning(f"Environment variable {var} is not set or empty.")

    # Check critical directories exist or create them
    for d in REQUIRED_DIRS:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {d}: {e}")
        else:
            if not os.path.isdir(d):
                logger.error(f"Configured path is not a directory: {d}")

    # Log summary
    logger.info("Safety checks completed.")
