# app/utils/stripe_client.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Subscription, SubscriptionStatus

# --- Optional Stripe setup ----------------------------------------------------
_STRIPE_API_KEY = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
try:
    import stripe  # type: ignore

    stripe.api_key = _STRIPE_API_KEY or None
except Exception:  # pragma: no cover
    stripe = None  # type: ignore


def _stripe_enabled() -> bool:
    """Return True if stripe SDK is importable and an API key is set."""
    return bool(stripe and _STRIPE_API_KEY)


# --- Public helpers used by routes / utils/__init__ ---------------------------


def create_checkout_session(
    user_id: int,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session for a subscription.
    Returns a simple demo object if Stripe is not configured.
    """
    if not _stripe_enabled():
        # Demo fallback so the app doesn't crash in dev
        return {
            "id": "cs_demo_123",
            "url": cancel_url,  # no real redirect in demo mode
            "mode": "subscription",
            "demo": True,
        }

    session = stripe.checkout.Session.create(  # type: ignore[attr-defined]
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user_id)},
        customer_creation="if_required",
        allow_promotion_codes=True,
    )
    return dict(session)


def get_billing_portal_url(customer_id: str, return_url: str) -> str:
    """
    Create a Stripe Billing Portal session and return its URL.
    Demo fallback just returns the provided return_url.
    """
    if not _stripe_enabled():
        return return_url

    portal = stripe.billing_portal.Session.create(  # type: ignore[attr-defined]
        customer=customer_id,
        return_url=return_url,
    )
    return str(portal.get("url") or return_url)


def cancel_stripe_subscription(subscription_id: str) -> bool:
    """
    Cancel an active subscription (at period end).
    Returns True on success; False in demo/no-stripe mode.
    """
    if not _stripe_enabled():
        return False

    stripe.Subscription.modify(  # type: ignore[attr-defined]
        subscription_id,
        cancel_at_period_end=True,
    )
    return True


# --- Webhook/DB sync ----------------------------------------------------------


def _coerce_ts(ts: Any) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(int(ts)) if ts else None
    except Exception:
        return None


def sync_subscription_from_stripe(event_or_object: dict[str, Any]) -> None:
    """
    Upsert a local Subscription row from a Stripe subscription object or event.
    Safe no-op if we cannot infer a user_id.
    """
    obj = (
        event_or_object.get("data", {}).get("object", {})
        if isinstance(event_or_object, dict) and "data" in event_or_object
        else event_or_object
    )
    if not isinstance(obj, dict):
        return

    metadata = obj.get("metadata") or {}
    user_id_str = str(metadata.get("user_id", "")).strip()
    user_id = int(user_id_str) if user_id_str.isdigit() else 0
    if not user_id:
        return

    sub_id = (obj.get("id") or "").strip()
    cust_id = (obj.get("customer") or "").strip()

    plan = obj.get("plan") or {}
    plan_name = plan.get("nickname") or plan.get("id") or ""

    status_value = (obj.get("status") or "").lower()
    try:
        mapped_status = SubscriptionStatus(status_value)
    except Exception:
        mapped_status = SubscriptionStatus.incomplete

    started_at = _coerce_ts(obj.get("start_date"))
    current_period_end = _coerce_ts(obj.get("current_period_end"))

    if not (sub_id and cust_id and plan_name and status_value):
        return

    db: Session = SessionLocal()
    try:
        sub = (
            db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()
        )
        if not sub:
            sub = Subscription(user_id=user_id)
            db.add(sub)

        def set_if_has(attr: str, value: Any) -> None:
            if hasattr(sub, attr):
                setattr(sub, attr, value)

        set_if_has("stripe_subscription_id", sub_id)
        set_if_has("stripe_customer_id", cust_id)
        set_if_has("plan_name", plan_name)
        set_if_has("status", mapped_status)
        set_if_has("started_at", started_at)
        set_if_has("current_period_end", current_period_end)

        if hasattr(sub, "updated_at"):
            setattr(sub, "updated_at", datetime.utcnow())

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# --- Backwards-compatible aliases (match older import names) ------------------


def create_stripe_checkout_session(
    user_id: int,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> dict[str, Any]:
    """Alias kept for older code paths."""
    return create_checkout_session(user_id, price_id, success_url, cancel_url)


def get_stripe_billing_portal_url(customer_id: str, return_url: str) -> str:
    """Alias kept for older code paths."""
    return get_billing_portal_url(customer_id, return_url)


__all__ = [
    "create_checkout_session",
    "create_stripe_checkout_session",
    "get_billing_portal_url",
    "get_stripe_billing_portal_url",
    "cancel_stripe_subscription",
    "sync_subscription_from_stripe",
]
