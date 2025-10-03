# app/main.py
import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext

# Optional: Stripe debug + session creator
try:
    import stripe  # type: ignore
except Exception:  # stripe not installed during early boot
    stripe = None  # noqa: N816

APP_NAME = "EchoScript.AI API"
API_PREFIX = "/api"

# -----------------------------------------------------------------------------
# Config / ENV
# -----------------------------------------------------------------------------
ENV = os.getenv("ENV", "production")
PORT = int(os.getenv("PORT", "8080"))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO") or os.getenv("STRIPE_PRO_PRICE_ID")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM")
STRIPE_PRICE_EDU = os.getenv("STRIPE_PRICE_EDU")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://echoscript.ai/success?session_id={CHECKOUT_SESSION_ID}")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://echoscript.ai/purchase")

if stripe and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Accept both explicit ALLOW_ORIGINS and VITE origin (netlify)
allow_origins_env = os.getenv("ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS")
ALLOW_ORIGINS = [o.strip() for o in (allow_origins_env or "https://echoscript.ai,https://www.echoscript.ai").split(",")]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Minimal in-memory user store so you can live-test signup/login now.
# Replace with Postgres model soon.
_fake_users = {}  # email -> {"email":..., "password_hash":...}


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class SignupIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -----------------------------------------------------------------------------
# Auth helpers
# -----------------------------------------------------------------------------
def create_token(email: str) -> str:
    payload = {"sub": email}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def get_current_email(authorization: Optional[str] = None) -> Optional[str]:
    """Very small helper to read a Bearer token and return the email (sub)."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# -----------------------------------------------------------------------------
# Health / root
# -----------------------------------------------------------------------------
@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return f"{APP_NAME} is up"


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": "live", "env": ENV}


# -----------------------------------------------------------------------------
# Auth: /api/auth/signup + /api/auth/login
# -----------------------------------------------------------------------------
@app.post(f"{API_PREFIX}/auth/signup", response_model=TokenOut)
def signup(body: SignupIn):
    email = body.email.lower().strip()
    if email in _fake_users:
        raise HTTPException(status_code=400, detail="User already exists")
    _fake_users[email] = {"email": email, "password_hash": hash_password(body.password)}
    return TokenOut(access_token=create_token(email))


@app.post(f"{API_PREFIX}/auth/login", response_model=TokenOut)
def login(body: LoginIn):
    email = body.email.lower().strip()
    user = _fake_users.get(email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenOut(access_token=create_token(email))


# -----------------------------------------------------------------------------
# Transcribe (temporary stub so the UI can proceed)
# Replace with your Whisper pipeline when ready.
# -----------------------------------------------------------------------------
@app.post(f"{API_PREFIX}/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Consume file stream so the client sees progress; discard in stub mode
    await file.read()
    return {
        "id": "stub-" + file.filename,
        "status": "completed",
        "text": "This is a placeholder transcript (wire Whisper next).",
        "language": "en",
        "duration_sec": None,
    }


# -----------------------------------------------------------------------------
# Stripe helpers
# -----------------------------------------------------------------------------
@app.get(f"{API_PREFIX}/stripe/_debug-env")
def stripe_debug_env():
    return {
        "ok": True,
        "mode_default": "subscription",
        "has_secret": bool(STRIPE_SECRET_KEY),
        "has_public": bool(os.getenv("STRIPE_PUBLIC_KEY")),
        "price_pro": bool(STRIPE_PRICE_PRO),
        "price_premium": bool(STRIPE_PRICE_PREMIUM),
        "price_edu": bool(STRIPE_PRICE_EDU),
        "success_url": STRIPE_SUCCESS_URL,
        "cancel_url": STRIPE_CANCEL_URL,
        "frontend": "https://echoscript.ai",
        "env": ENV,
    }


@app.post(f"{API_PREFIX}/stripe/create-checkout-session")
def create_checkout_session(plan: dict):
    """
    Body example: { "plan": "pro" }
    Valid: "pro" | "premium" | "edu"
    """
    if not stripe or not STRIPE_SECRET_KEY:
        raise HTTPException(400, "Stripe is not configured")

    plan_key = (plan or {}).get("plan", "pro")
    price_lookup = {
        "pro": STRIPE_PRICE_PRO,
        "premium": STRIPE_PRICE_PREMIUM,
        "edu": STRIPE_PRICE_EDU,
    }
    price_id = price_lookup.get(plan_key)
    if not price_id:
        raise HTTPException(400, f"Unknown plan '{plan_key}'")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=STRIPE_SUCCESS_URL,
        cancel_url=STRIPE_CANCEL_URL,
    )
    return {"url": session.get("url")}

