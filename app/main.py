""""Main entrypoint for EchoScript.AI FastAPI backend."""

import os
import platform
import sys

import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.contact import router as contact_router
from app.routes.export import router as export_router
from app.routes.feedback import router as feedback_router
from app.routes.history import router as history_router
from app.routes.newsletter import router as newsletter_router
from app.routes.password_reset import router as password_reset_router
from app.routes.signup import router as signup_router
from app.routes.stripe_webhook import router as stripe_webhook_router
from app.routes.subscription import router as subscription_router
from app.routes.summary import router as summary_router
from app.routes.transcribe import router as transcribe_router
from app.routes.transcripts import router as transcripts_router
from app.routes.translate import router as translate_router
from app.routes.verify_email import router as verify_email_router
from app.routes.video_task import router as video_task_router
from app.utils.safety_check import run_safety_checks
from app.ws.socket_transcriber import websocket_endpoint

# === Windows-specific DLL patch for Torch ===
if sys.platform == "win32":
    torch_dll_dir = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
    if os.path.isdir(torch_dll_dir):
        os.add_dll_directory(torch_dll_dir)

# === Load environment variables ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*").strip()

# === Initialize FastAPI ===
app = FastAPI(
    title="EchoScript.AI Backend",
    version="0.1.0",
    description="Production-grade transcription backend supporting WhisperX, subscriptions, and more.",
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Safety Checks ===
run_safety_checks()

# === Register Routers ===
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(signup_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(verify_email_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(password_reset_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscription_router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(stripe_webhook_router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(transcribe_router, prefix="/api/transcribe", tags=["Transcription"])
app.include_router(video_task_router, prefix="/api/video-task", tags=["Video"])
app.include_router(transcripts_router, prefix="/api/transcripts", tags=["Transcripts"])
app.include_router(export_router, prefix="/api/export", tags=["Export"])
app.include_router(contact_router, prefix="/api/contact", tags=["Contact"])
app.include_router(newsletter_router, prefix="/api/newsletter", tags=["Newsletter"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(translate_router, prefix="/api/translate", tags=["Translation"])
app.include_router(summary_router, prefix="/api/summary", tags=["Summarization"])
app.include_router(history_router, prefix="/api/history", tags=["History"])

# === WebSocket Endpoint ===
app.websocket("/ws/transcribe")(websocket_endpoint)

# === Health Check Endpoint ===
@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "platform": platform.system(),
        "torch_cuda": torch.cuda.is_available(),
        "hf_token_loaded": bool(HF_TOKEN),
    }

