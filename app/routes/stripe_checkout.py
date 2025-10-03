from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import stripe  # type: ignore[attr-defined]
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.dependencies import get_current_user
from app.models.subscription import (  # or from app.models import Subscription if that's your path
    Subscription,
)

# Optionally load .env so this module works even if main didn't load it yet
try:
    from dotenv import load_dotenv  # pip install python-dotenv

    env_path = Path(__file__).resolve().parents[2] / ".env"  # Backend/.env
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    if val is None:
        return default
    val = val.strip()
    return val if val else default


def _ensure_stripe_configured() -> None:
    key = _get_env("STRIPE_SECRET_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe.api_key = key


# Defaults / config
STRIPE_MODE_DEFAULT = (
    _get_env("STRIPE_MODE", "subscription") or "subscription"
).lower()
CURRENCY = (_get_env("STRIPE_CURRENCY", "usd") or "usd").lower()

# Frontend URLs (support either FRONTEND_URL or FRONTEND_DOMAIN)
_FRONTEND = (
    _get_env("FRONTEND_URL") or _get_env("FRONTEND_DOMAIN") or "http://localhost:5173"
)
SUCCESS_URL = _get_env(
    "STRIPE_SUCCESS_URL", f"{_FRONTEND}/success?session_id={{CHECKOUT_SESSION_ID}}"
)
CANCEL_URL = _get_env("STRIPE_CANCEL_URL", f"{_FRONTEND}/purchase")

# Dashboard Price IDs (preferred)
PRICE_MAP: Dict[str, Optional[str]] = {
    "pro": _get_env("STRIPE_PRICE_PRO"),
    "premium": _get_env("STRIPE_PRICE_PREMIUM"),
    "edu": _get_env("STRIPE_PRICE_EDU"),
}

# Fallback inline pricing (cents) if you haven't created Prices yet
AMOUNT_CENTS: Dict[str, int] = {"pro": 999, "premium": 1999, "edu": 499}


def _get_user_id(u: Any) -> int:
    return u["id"] if isinstance(u, dict) else int(getattr(u, "id"))


def _get_user_email(u: Any) -> Optional[str]:
    return u.get("email") if isinstance(u, dict) else getattr(u, "email", None)


@router.post("/create-checkout-session")
async def create_checkout_session(
    req: Request, current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    _ensure_stripe_configured()

    try:
        body = await req.json()
    except Exception:
        body = {}
    plan = str((body.get("plan") or "pro")).lower()
    if plan not in {"pro", "premium", "edu"}:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{plan}'")

    mode = (
        STRIPE_MODE_DEFAULT
        if STRIPE_MODE_DEFAULT in {"subscription", "payment"}
        else "subscription"
    )
    price_id = PRICE_MAP.get(plan)

    user_id = _get_user_id(current_user)
    user_email = _get_user_email(current_user) or ""

    db: Session = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        customer_id = sub.stripe_customer_id if sub and sub.stripe_customer_id else None

        if not customer_id:
            customer = stripe.Customer.create(  # type: ignore[attr-defined]
                email=user_email,
                metadata={"user_id": str(user_id)},
            )
            customer_id = customer["id"]
            if not sub:
                sub = Subscription(
                    user_id=user_id
                )  # don't set plan/status yet; webhook will
                db.add(sub)
            sub.stripe_customer_id = customer_id
            db.commit()

        if price_id:
            line_items = [{"price": price_id, "quantity": 1}]
        else:
            amount = AMOUNT_CENTS.get(plan, 999)
            price_data: Dict[str, Any] = {
                "currency": CURRENCY,
                "product_data": {"name": f"EchoScript {plan.capitalize()}"},
                "unit_amount": amount,
            }
            if mode == "subscription":
                price_data["recurring"] = {"interval": "month"}
            line_items = [{"price_data": price_data, "quantity": 1}]

        session = stripe.checkout.Session.create(  # type: ignore[attr-defined]
            mode=mode,
            customer=customer_id,
            line_items=line_items,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            allow_promotion_codes=True,
            metadata={"user_id": str(user_id)},  # on session
            subscription_data={
                "metadata": {"user_id": str(user_id)}
            },  # on subscription
        )
        return {"url": session["url"]}
    except stripe.error.StripeError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/_debug-env")
def debug_env() -> Dict[str, Any]:
    return {
        "has_secret": bool(_get_env("STRIPE_SECRET_KEY")),
        "mode_default": STRIPE_MODE_DEFAULT,
        "currency": CURRENCY,
        "price_pro": (PRICE_MAP["pro"][:8] + "…") if PRICE_MAP.get("pro") else None,
        "price_premium": (
            (PRICE_MAP["premium"][:8] + "…") if PRICE_MAP.get("premium") else None
        ),
        "price_edu": (PRICE_MAP["edu"][:8] + "…") if PRICE_MAP.get("edu") else None,
        "success_url": SUCCESS_URL,
        "cancel_url": CANCEL_URL,
        "frontend": _FRONTEND,
    }
