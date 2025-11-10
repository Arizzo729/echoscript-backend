# asgi_dev.py — dev API with lazy Whisper loading and python-jose JWT
# Includes all endpoints from main.py + /api/video-task endpoint (video transcription/subtitle)
# - Avoids heavy ASR loading at startup
# - Secure JWT auth
# - Compatible with VideoUpload.jsx frontend
# - Includes all routes from main.py for complete API access

import os
import uuid
import logging
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy import text as sqla_text
from sqlalchemy.orm import Session, declarative_base, sessionmaker



load_dotenv(".env")

# EmailStr moved between pydantic versions; try common locations then fall back to plain str
try:
    from pydantic import EmailStr  # type: ignore
except Exception:
    try:
        from pydantic.networks import EmailStr  # type: ignore
    except Exception:
        EmailStr = str  # type: ignore

# ---------- config ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
# SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "dev-secret-change-me")
SECRET_KEY = os.getenv("JWT_SECRET_KEY") 
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALLOW_ORIGINS = [o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",")]
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "data")).resolve()

ASGI_ENABLE_TRANSCRIBE = os.getenv("ASGI_ENABLE_TRANSCRIBE", "1") == "1"
ASGI_LOAD_MODEL = os.getenv("ASGI_LOAD_MODEL", "0") == "1"
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
ENV_DEVICE = os.getenv("WHISPER_DEVICE")
ENV_COMPUTE = os.getenv("WHISPER_COMPUTE")

# ---------- db ----------
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- models ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(String, nullable=False, server_default="free")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=sqla_text("CURRENT_TIMESTAMP"))


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="queued")
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=sqla_text("CURRENT_TIMESTAMP"))

# ---------- schemas ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JobOut(BaseModel):
    job_id: str
    status: str
    filename: str
    transcript: str | None = None


# ---------- helpers ----------
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(sub: int | str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(sub), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def pick_device_and_compute() -> tuple[str, str]:
    if ENV_DEVICE:
        return ENV_DEVICE, (ENV_COMPUTE or ("float16" if ENV_DEVICE == "cuda" else "int8"))
    try:
        import ctranslate2 as ct2
        if getattr(ct2, "get_cuda_device_count", lambda: 0)() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def has_onnxruntime() -> bool:
    try:
        import onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


# ---------- app ----------
APP_VERSION = os.getenv("GIT_SHA", "0.7-dev")
app = FastAPI(title="EchoScript API", version=APP_VERSION)

def _allowed_origins() -> list[str]:
    raw = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)

WHISPER = None
VAD_ENABLED = False
DEVICE = "cpu"
COMPUTE = "int8"


def _load_model_if_needed():
    """Lazy-load Whisper only when required (or if ASGI_LOAD_MODEL=1)."""
    global WHISPER, VAD_ENABLED, DEVICE, COMPUTE
    if WHISPER is not None:
        return
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        raise RuntimeError(
            "Whisper not installed or import failed. "
            "Install faster-whisper and its dependencies.\n"
            f"Original error: {e}"
        )
    DEVICE, COMPUTE = pick_device_and_compute()
    VAD_ENABLED = has_onnxruntime()
    WHISPER = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=ENV_COMPUTE or COMPUTE)


@app.on_event("startup")
def on_startup():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if ASGI_LOAD_MODEL and ASGI_ENABLE_TRANSCRIBE:
        _load_model_if_needed()
    _mount_all_routes()


@app.get("/")
def root_ok() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/api/healthz")
def api_health_ok() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health_ok() -> str:
    return "ok"


@app.get("/healthz")
def healthz():
    with engine.connect() as conn:
        conn.execute(sqla_text("select 1"))
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": ENV_COMPUTE or COMPUTE,
        "vad": VAD_ENABLED,
        "transcribe_enabled": ASGI_ENABLE_TRANSCRIBE,
        "whisper_loaded": WHISPER is not None,
    }


@app.get("/__whoami")
def whoami():
    return {"file": __file__, "version": app.version}


# ---------- mount all routes from main.py ----------
CONTACT_ROUTER_MOUNTED = False

def _mount_all_routes():
    """Mount all routes from app.routes modules (same as main.py)"""
    global CONTACT_ROUTER_MOUNTED
    modules = [
        "app.routes.health",
        "app.routes.contact",
        "app.routes.newsletter",
        "app.routes.auth",
        "app.routes.history",
        "app.routes.export",
        "app.routes.signup",
        "app.routes.password_reset",
        "app.routes.send_reset",
        "app.routes.paypal",
        "app.routes.paypal_health",
        "app.routes.assistant",
        "app.routes.transcripts",
        "app.routes.usage",
    ]
    for prefix in ["/api/v1", "/v1"]:
        for mod in modules:
            try:
                m = importlib.import_module(mod)
                router = getattr(m, "router")
                app.include_router(router, prefix=prefix)
                if mod.endswith(".contact"):
                    CONTACT_ROUTER_MOUNTED = True
                log.info("Mounted %s at %s", mod, prefix)
            except Exception as e:
                log.warning("Skipping %s: %s", mod, e)
    
    # Compat routes that already have absolute paths
    try:
        from app.routes import compact_endpoints as compat
        app.include_router(compat.router)
        log.info("Mounted compat endpoints without prefix")
    except Exception as e:
        log.warning("Compat endpoints not mounted: %s", e)
    
    try:
        from app.routes.feedback import router as feedback_router
        app.include_router(feedback_router)
        log.info("Mounted feedback router at its absolute path")
    except Exception as e:
        log.warning("Feedback endpoints not mounted: %s", e)
    
    # Stripe payment routes
    try:
        from app.routes.stripe import router as stripe_router
        app.include_router(stripe_router, prefix="/api")
        log.info("Mounted Stripe router at /api/stripe")
    except Exception as e:
        log.warning("Stripe endpoints not mounted: %s", e)

    try:
        from app.routes.stripe_checkout import router as stripe_checkout_router
        app.include_router(stripe_checkout_router)
        log.info("Mounted Stripe checkout router at /api/stripe/checkout")
    except Exception as e:
        log.warning("Stripe checkout endpoints not mounted: %s", e)

    try:
        from app.routes.stripe_webhook import router as stripe_webhook_router
        app.include_router(stripe_webhook_router)
        log.info("Mounted Stripe webhook router at /api/stripe/webhook")
    except Exception as e:
        log.warning("Stripe webhook endpoints not mounted: %s", e)
    
    # Fallback contact if needed
    if not CONTACT_ROUTER_MOUNTED:
        _add_fallback_contact()
    
    # Add diagnostics
    _add_diagnostics()


def _add_fallback_contact():
    """Add fallback contact endpoint if main contact router didn't load"""
    try:
        from app.utils.send_email import send_email, EmailError
    except ImportError:
        log.warning("send_email module not available, skipping fallback contact")
        return
    
    class _ContactIn(BaseModel):
        name: str
        email: EmailStr
        subject: str
        message: str
        hp: Optional[str] = None
        to: Optional[EmailStr] = None

    def _contact_to_default() -> str:
        return os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai"

    def _send_contact_email(payload: dict) -> None:
        subj = f"[EchoScript Contact] {payload.get('subject','(no subject)')}"
        text = (
            "New contact submission:\n\n"
            f"Name: {payload.get('name')}\n"
            f"Email: {payload.get('email')}\n"
            f"Subject: {payload.get('subject')}\n\n"
            f"Message:\n{payload.get('message')}\n"
        )
        html = (
            f"<h2>New contact submission</h2>"
            f"<p><b>Name:</b> {payload.get('name')}</p>"
            f"<p><b>Email:</b> {payload.get('email')}</p>"
            f"<p><b>Subject:</b> {payload.get('subject')}</p>"
            f"<hr/><pre style='white-space:pre-wrap'>{payload.get('message')}</pre>"
        )
        to_addr = payload.get("to") or _contact_to_default()
        send_email(to_addr, subj, text, html, reply_to=payload.get("email"))

    @app.post("/api/contact")
    async def _contact_fallback_api(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        bg.add_task(_send_contact_email, body.model_dump())
        return {"ok": True, "status": "accepted"}

    @app.post("/v1/contact")
    async def _contact_fallback_v1(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        bg.add_task(_send_contact_email, body.model_dump())
        return {"ok": True, "status": "accepted"}
    
    log.info("Mounted fallback contact endpoints")


def _add_diagnostics():
    """Add diagnostic endpoints"""
    diag = APIRouter(prefix="/_diag", tags=["diag"])

    @diag.get("/email")
    def diag_email():
        have_resend = bool(os.getenv("RESEND_API_KEY"))
        have_smtp = all(bool(os.getenv(k)) for k in ["SMTP_HOST","SMTP_PORT","SMTP_USER","SMTP_PASS","SMTP_FROM"])
        mode = "HTTP" if have_resend else ("SMTP" if have_smtp else "NONE")
        return {
            "mode": mode,
            "resend_api_key_present": have_resend,
            "smtp_config_present": have_smtp,
            "to": os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai",
            "from": os.getenv("EMAIL_FROM") or os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM") or "noreply@onresend.com",
        }

    app.include_router(diag, prefix="/api")
    
    @app.post("/api/contact/test")
    def contact_test():
        try:
            from app.utils.send_email import send_email, EmailError
            send_email(
                to_address=os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai",
                subject="EchoScript email test",
                body_text="If you see this, HTTP email is working ✅",
                body_html="<p>If you see this, <b>HTTP email</b> is working ✅</p>",
                reply_to="no-reply@echoscript.ai",
            )
            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    log.info("Mounted diagnostics endpoints")


@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    row = (
        db.execute(select(User).where(User.email == form_data.username.lower()))
        .scalars()
        .first()
    )
    if not row or not verify_password(form_data.password, row.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    return Token(access_token=create_access_token(sub=row.id))


# ---------- transcription ----------
def _transcribe_file(audio_path: Path, language: str | None = "en") -> str:
    _load_model_if_needed()
    segments, _info = WHISPER.transcribe(
        str(audio_path),
        beam_size=5,
        best_of=1,
        vad_filter=VAD_ENABLED,
        language=language,
        temperature=0.0,
        condition_on_previous_text=True,
    )
    parts = [
        getattr(seg, "text", "").strip()
        for seg in segments
        if getattr(seg, "text", "").strip()
    ]
    return (" ".join(parts)).strip() or "(empty transcript)"


@app.post("/api/v1/transcribe", response_model=JobOut)
async def transcribe(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    language: str | None = "en",
    authorization: Optional[str] = Header(None)
):
    if not ASGI_ENABLE_TRANSCRIBE:
        raise HTTPException(status_code=503, detail="transcription_disabled")

    # Try to get current user from authorization header
    current_user_id = None
    try:
        from app.dependencies import get_current_user
        from app.models import Transcript, User
        from fastapi import Header, Request
        from jose import jwt, JWTError
        
        # Try to extract token from Authorization header
        token = authorization
        if token and token.startswith("Bearer "):
            token = token[7:]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    current_user_id = int(user_id)
                    log.info(f"Authenticated user_id={current_user_id} for transcription")
            except (JWTError, ValueError, TypeError) as e:
                log.warning(f"Could not decode JWT token: {e}")
    except Exception as e:
        log.warning(f"Could not authenticate user: {e}")

    ext = Path(file.filename).suffix.lower() or ".bin"
    job_id = str(uuid.uuid4())
    target = STORAGE_DIR / f"{job_id}{ext}"

    file_size = 0
    with target.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            file_size += len(chunk)

    db.add(Job(id=job_id, filename=target.name, status="processing", transcript=None))
    db.commit()

    try:
        text = _transcribe_file(target, language=language)
        db.execute(
            sqla_text("UPDATE jobs SET status=:s, transcript=:t WHERE id=:i"),
            {"s": "done", "t": text, "i": job_id},
        )
        db.commit()
        
        # ALSO save to transcripts table for authenticated users
        if current_user_id:
            try:
                from app.models import Transcript
                
                transcript = Transcript(
                    user_id=current_user_id,
                    title=file.filename or f"Transcript {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    original_filename=file.filename,
                    storage_filename=target.name,
                    content=text,
                    duration=None,
                    file_size=file_size,
                    language=language if language != "auto" else "en",
                    status="completed"
                )
                
                db.add(transcript)
                db.commit()
                db.refresh(transcript)
                log.info(f"Transcript saved to transcripts table with id={transcript.id} for user={current_user_id}")
            except Exception as e:
                log.error(f"Failed to save to transcripts table: {e}")
                # Don't fail the request if transcript save fails
        else:
            log.info(f"No authenticated user, transcript only saved to jobs table")
        
        return JobOut(job_id=job_id, status="done", filename=target.name, transcript=text)
    except Exception as e:
        import logging
        logging.exception(f"transcription_failed for job {job_id}")
        db.execute(
            sqla_text("UPDATE jobs SET status=:s, transcript=:t WHERE id=:i"),
            {"s": "error", "t": f"transcription_error: {e}", "i": job_id},
        )
        db.commit()
        return JSONResponse(status_code=500, content={"detail": "transcription_failed", "job_id": job_id, "error": str(e)})


# ---------- video-task endpoint for VideoUpload.jsx ----------
@app.post("/api/video-task")
async def video_task(
    file: UploadFile = File(...),
    task_type: str = Form("transcription"),
    language: str = Form("auto"),
):
    """Handles both transcription and subtitle generation from video upload."""
    if not ASGI_ENABLE_TRANSCRIBE:
        raise HTTPException(status_code=503, detail="transcription_disabled")

    ext = Path(file.filename).suffix.lower() or ".mp4"
    job_id = str(uuid.uuid4())
    video_path = STORAGE_DIR / f"{job_id}{ext}"

    with video_path.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    try:
        result_text = _transcribe_file(video_path, language=language)
        if task_type == "subtitles":
            # Basic SRT formatting
            subtitles = "\n".join(
                [f"{i+1}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{line}" for i, line in enumerate(result_text.split("."))]
            )
            return {"status": "success", "subtitles": subtitles}
        return {"status": "success", "transcript": result_text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"video_task_failed: {e}")
