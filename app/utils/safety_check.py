# app/utils/safety_check.py

import os
from app.config import config, redis_client
from app.utils.logger import logger

def run_safety_checks():
    # === Env Vars ===
    required_env_vars = ["OPENAI_API_KEY", "JWT_SECRET_KEY", "REDIS_URL", "DATABASE_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.critical(f"[❌ CONFIG] Missing required environment variables: {missing_vars}")
        raise SystemExit("Startup halted. Required environment variables not set.")

    # === Redis Connection ===
    if not redis_client or not redis_client.ping():
        logger.critical("[❌ REDIS] Connection to Redis failed. Check REDIS_URL and service status.")
        raise SystemExit("Startup halted. Redis unavailable.")

    logger.info("[✅ SAFETY] All core systems passed initial checks.")
