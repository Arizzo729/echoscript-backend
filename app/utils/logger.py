# ---- EchoScript.AI: utils/logger.py ----

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.config import Config

# Avoid reinitializing logger in reload environments (e.g. Uvicorn dev mode)
if Config.APP_NAME in logging.root.manager.loggerDict:
    logger = logging.getLogger(Config.APP_NAME)
else:
    logger = logging.getLogger(Config.APP_NAME)
    logger.setLevel(Config.LOG_LEVEL.upper())

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Console Logging ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Rotating File Logging ---
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        filename="logs/echoscript.log",
        maxBytes=5_000_000,  # 5MB
        backupCount=3        # Keep 3 old logs
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("✅ Logger initialized for EchoScript.AI")
