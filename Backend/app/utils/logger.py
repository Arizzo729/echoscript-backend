import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import config

# Ensure log directory exists
os.makedirs(config.LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger("echoscript")
logger.setLevel(
    config.LOG_LEVEL.upper() if isinstance(config.LOG_LEVEL, str) else logging.INFO
)

# Formatter for all handlers
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(
    config.LOG_LEVEL.upper() if isinstance(config.LOG_LEVEL, str) else logging.INFO
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Rotating file handler
log_file = os.path.join(config.LOG_DIR, "echoscript.log")
file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=5,  # keep up to 5 log files
    encoding="utf-8",
)
file_handler.setLevel(
    config.LOG_LEVEL.upper() if isinstance(config.LOG_LEVEL, str) else logging.INFO
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Example usage: logger.info("Logger initialized")
