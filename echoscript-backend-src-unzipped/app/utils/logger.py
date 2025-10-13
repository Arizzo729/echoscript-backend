# app/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.settings import settings

# Create a single logger instance
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(settings.LOG_LEVEL.upper())

# Create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create rotating file handler if LOG_DIR is set
log_dir = Path(settings.LOG_DIR)
if log_dir:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.info("Logger initialized.")