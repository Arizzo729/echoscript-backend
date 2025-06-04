# ---- EchoScript.AI: utils/logger.py ----

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.config import Config

# Prevent reinitialization in hot reload environments
if Config.APP_NAME in logging.root.manager.loggerDict:
    logger = logging.getLogger(Config.APP_NAME)
else:
    logger = logging.getLogger(Config.APP_NAME)
    logger.setLevel(Config.LOG_LEVEL.upper())

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ---- Console Output ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ---- Rotating File Output ----
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        filename="logs/echoscript.log",
        maxBytes=5_000_000,  # 5MB max per file
        backupCount=3        # Keep up to 3 log files
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("✅ Logger initialized for EchoScript.AI")
