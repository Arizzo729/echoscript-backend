"""
app/utils package: helper modules for EchoScript.AI backend.
"""

from .auth_utils import create_access_token, decode_access_token, hash_password, verify_password
from .db_utils import get_user_by_email, update_user_password
from .export_utils import generate_export_file
from .file_helpers import list_transcripts, load_transcript_file, save_transcript_file
from .logger import logger
from .redis_client import redis_client
from .safety_check import run_safety_checks
from .send_email import send_email
from .stripe_client import (
    cancel_stripe_subscription,
    create_stripe_checkout_session,
    sync_subscription_from_stripe,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_user_by_email",
    "update_user_password",
    "logger",
    "redis_client",
    "save_transcript_file",
    "load_transcript_file",
    "list_transcripts",
    "generate_export_file",
    "create_stripe_checkout_session",
    "cancel_stripe_subscription",
    "sync_subscription_from_stripe",
    "send_email",
    "summarize_transcript",
    "analyze_sentiment",
    "extract_keywords",
    "translate_text",
    "clean_transcript",
    "run_safety_checks",
]
