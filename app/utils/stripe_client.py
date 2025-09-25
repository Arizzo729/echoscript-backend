# app/utils/stripe_client.py - replace sync_subscription_from_stripe with this version
from datetime import datetime
from typing import Any, Optional, cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Subscription, SubscriptionStatus


def _coerce_ts(ts: Any) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(int(ts)) if ts else None
    except Exception:
        return None


def sync_subscription_from_stripe(event_or_object: dict[str, Any]) -> None:
    obj = (
        event_or_object.get("data", {}).get("object", {})
        if "data" in event_or_object
        else event_or_object
    )
    metadata = obj.get("metadata") or {}
    user_id_str = str(metadata.get("user_id", "")).strip()
    user_id = int(user_id_str) if user_id_str.isdigit() else 0
    if not user_id:
        return  # cannot map to a local user safely

    sub_id = (obj.get("id") or "").strip()
    cust_id = (obj.get("customer") or "").strip()
    plan_name = (obj.get("plan", {}) or {}).get("nickname") or (
        obj.get("plan", {}) or {}
    ).get("id")
    status_value = (obj.get("status") or "").lower()

    # If critical fields are missing, defer creating/updating to a later webhook
    if not (sub_id and cust_id and plan_name and status_value):
        return

    # Map status safely to lowercase Enum
    try:
        mapped_status = SubscriptionStatus(status_value)
    except Exception:
        mapped_status = SubscriptionStatus.incomplete

    started_at = _coerce_ts(obj.get("start_date"))
    current_period_end = _coerce_ts(obj.get("current_period_end"))

    db: Session = SessionLocal()
    try:
        sub = (
            db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()
        )
        if not sub:
            sub = Subscription(
                user_id=user_id,
                stripe_subscription_id=sub_id,
                stripe_customer_id=cust_id,
                plan_name=plan_name,
                status=mapped_status,
                started_at=started_at or datetime.utcnow(),
            )
            db.add(sub)
        else:
            sub.stripe_subscription_id = sub_id
            sub.stripe_customer_id = cust_id
            sub.plan_name = plan_name
            sub.status = mapped_status
            if started_at:
                sub.started_at = started_at
        if current_period_end:
            sub.renewed_at = current_period_end
        if mapped_status in {SubscriptionStatus.canceled, SubscriptionStatus.unpaid}:
            sub.canceled_at = datetime.utcnow()

        db.commit()
    finally:
        db.close()
