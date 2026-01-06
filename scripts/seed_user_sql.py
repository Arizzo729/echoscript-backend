# scripts/seed_user_sql.py
"""
Compatibility wrapper: delegates to scripts/seed_user.py with defaults.
Keeps older docs/commands working but uses the current ORM & models.
"""
from scripts.seed_user import main

if __name__ == "__main__":
    main("Echoscript.AI@Outlook.com", "SunnySideUp!", plan="free")
