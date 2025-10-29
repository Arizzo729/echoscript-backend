import argparse
import logging
import os
import sys
from datetime import datetime

# 1) Load .env (for DATABASE_URL)
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from passlib.context import CryptContext
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError, ProgrammingError, SQLAlchemyError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def get_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if not url:
        print(
            "ERROR: DATABASE_URL not set. Ensure .env contains DATABASE_URL.",
            file=sys.stderr,
        )
        sys.exit(1)
    return create_engine(url, pool_pre_ping=True)


# Try common user table names in order
CANDIDATE_TABLES = ["users", "user", "user_account", "accounts", "auth_user"]

# Column name candidates
EMAIL_COLS = ["email", "user_email", "username", "login", "login_email"]
PWD_COLS = ["hashed_password", "password_hash", "password_hashed", "password"]
TRUE_FLAGS = [
    "is_active",
    "is_verified",
    "is_confirmed",
    "is_enabled",
    "enabled",
    "active",
    "verified",
    "email_verified",
    "is_superuser",
]
TS_CREATED = ["created_at", "created", "inserted_at"]
TS_UPDATED = ["updated_at", "updated", "modified_at"]


def find_first_column(columns: list[str], candidates: list[str]) -> str | None:
    existing = {c.name.lower(): c.name for c in columns}
    for cand in candidates:
        if cand in existing:
            return existing[cand]
    return None


def reflect_user_table(engine: Engine) -> Table:
    md = MetaData()
    inspector = inspect(engine)
    # Pick the first candidate that exists
    for name in CANDIDATE_TABLES:
        if name in inspector.get_table_names():
            tbl = Table(name, md, autoload_with=engine)
            logging.info(f"Using table: {name}")
            return tbl
    # Fallback: try to autoload 'users'
    try:
        tbl = Table("users", md, autoload_with=engine)
        logging.info("Using table: users")
        return tbl
    except Exception:
        available = inspector.get_table_names()
        raise NoSuchTableError(
            f"No user table found. Checked {CANDIDATE_TABLES}. Existing tables: {available}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Create or verify a user in the DB (no app.models import needed)."
    )
    parser.add_argument("email", type=str, help="Email / login")
    parser.add_argument("password", type=str, help="Plaintext password")
    args = parser.parse_args()

    email = args.email.strip().lower()
    plaintext = args.password

    engine = get_engine()
    try:
        user_table = reflect_user_table(engine)
    except NoSuchTableError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    cols = list(user_table.columns)
    email_col = find_first_column(cols, EMAIL_COLS)
    pwd_col = find_first_column(cols, PWD_COLS)

    if not email_col:
        print(
            f"ERROR: Could not detect an email/login column. Tried: {EMAIL_COLS}. Found columns: {[c.name for c in cols]}",
            file=sys.stderr,
        )
        sys.exit(3)
    if not pwd_col:
        print(
            f"ERROR: Could not detect a password column. Tried: {PWD_COLS}. Found columns: {[c.name for c in cols]}",
            file=sys.stderr,
        )
        sys.exit(4)

    # Optional columns (only set if present)
    true_flag_cols = [c for c in TRUE_FLAGS if c in {col.name for col in cols}]
    created_col = find_first_column(cols, TS_CREATED)
    updated_col = find_first_column(cols, TS_UPDATED)

    hpw = hash_password(plaintext)

    with engine.begin() as conn:
        # Check if the user already exists
        try:
            q = select(user_table).where(user_table.c[email_col] == email)
            existing = conn.execute(q).first()
        except Exception as e:
            print(f"ERROR querying for existing user: {e}", file=sys.stderr)
            sys.exit(5)

        if existing:
            print(f"??  User already exists: {email}")
            sys.exit(0)

        row = {email_col: email, pwd_col: hpw}
        for flag in true_flag_cols:
            row[flag] = True
        now = datetime.utcnow()
        if created_col:
            row[created_col] = now
        if updated_col:
            row[updated_col] = now

        try:
            conn.execute(user_table.insert().values(**row))
        except ProgrammingError:
            # If case sensitivity bites (e.g., quoted identifiers), try a raw SQL fallback
            cols_order = [email_col, pwd_col] + true_flag_cols
            if created_col:
                cols_order.append(created_col)
            if updated_col:
                cols_order.append(updated_col)
            placeholders = ", ".join([f":{c}" for c in cols_order])
            colnames = ", ".join(cols_order)
            sql = text(
                f'INSERT INTO "{user_table.name}" ({colnames}) VALUES ({placeholders})'
            )
            vals = {k: row[k] for k in cols_order}
            conn.execute(sql, vals)
        except SQLAlchemyError as e:
            print(f"ERROR inserting user: {e}", file=sys.stderr)
            raise

    print(
        f"? Created user: {email}  (email column: '{email_col}', password column: '{pwd_col}')"
    )


if __name__ == "__main__":
    main()
