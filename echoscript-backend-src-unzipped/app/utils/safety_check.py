# app/utils/safety_check.py
import os
from pathlib import Path

from app.core.settings import settings
from app.utils.logger import logger


def run_startup_safety_checks():
    """
    Performs safety checks on application startup.

    - Verifies that all required environment variables are set.
    - Ensures that necessary directories exist.
    """
    logger.info("Performing startup safety checks...")

    # --- Check for required environment variables ---
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
    ]
    missing_vars = [var for var in required_vars if not getattr(settings, var)]

    if missing_vars:
        for var in missing_vars:
            logger.error(f"Required environment variable is not set: {var}")
        raise RuntimeError("Missing required environment variables. Application cannot start.")

    # --- Check for optional but important variables ---
    if not settings.STRIPE_SECRET_KEY:
        logger.warning("STRIPE_SECRET_KEY is not set. Stripe integration will be disabled.")
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        logger.warning("PayPal client ID or secret is not set. PayPal integration will be disabled.")
    if not settings.RESEND_API_KEY and not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASS]):
        logger.warning("No email provider is configured. Email sending will not work.")

    # --- Ensure necessary directories exist ---
    required_dirs = [
        settings.UPLOAD_FOLDER,
        settings.STORAGE_DIR,
        settings.EXPORT_DIR,
        settings.LOG_DIR,
    ]

    for dir_path in required_dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create required directory {dir_path}: {e}")
            raise

    logger.info("Startup safety checks passed.")