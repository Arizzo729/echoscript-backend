# ---- EchoScript.AI Backend: main.py ----

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, platform, torch

# ---- Load environment variables ----
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- Initialize FastAPI App ----
app = FastAPI(
    title="EchoScript.AI Backend",
    version="2.8.0",
    description="Advanced AI transcription backend with WhisperX, GPT-4, speaker diarization, export, assistant, and more.",
)

# ---- CORS Configuration ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 Replace with frontend domain before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Route Imports ----
from app.routes.transcribe import router as transcribe_router
from app.routes.export import router as export_router
from app.routes.summary import router as summary_router
from app.routes.feedback import router as feedback_router
from app.routes.translate import router as translate_router
from app.routes.history import router as history_router
from app.routes.assistant import router as assistant_router
from app.auth.auth_routes import router as auth_router
from app.routes.send_reset_code import router as send_reset_code_router
from app.routes.verify_reset import router as verify_reset_router
from app.routes.security import router as security_router
from app.ws.socket_transcriber import websocket_endpoint
from app.routes.subscription import router as subscription_router
app.include_router(subscription_router, prefix="/api", tags=["subscription"])


# ---- Route Registration ----
app.include_router(auth_router,           prefix="/api/", tags=["Authentication"])
app.include_router(transcribe_router,     prefix="/api/", tags=["Transcription"])
app.include_router(export_router,         prefix="/api/", tags=["Export"])
app.include_router(summary_router,        prefix="/api/", tags=["Summarization"])
app.include_router(feedback_router,       prefix="/api/", tags=["Feedback"])
app.include_router(translate_router,      prefix="/api/", tags=["Translation"])
app.include_router(history_router,        prefix="/api/", tags=["Transcript History"])
app.include_router(assistant_router,      prefix="/api/", tags=["AI Assistant"])
app.include_router(send_reset_code_router, prefix="/api/", tags=["Password Reset"])
app.include_router(verify_reset_router,    prefix="/api/", tags=["Password Reset"])
app.include_router(security_router,        prefix="/api/", tags=["Security"])

# ---- WebSocket Transcription Endpoint ----
app.websocket("/ws/transcribe")(websocket_endpoint)

# ---- Health Check ----
@app.get("/")
async def root():
    return {
        "status": "ok",
        "platform": platform.system(),
        "torch_cuda": torch.cuda.is_available(),
        "hf_token_loaded": bool(HF_TOKEN),
        "openai_api_loaded": bool(OPENAI_API_KEY),
    }
