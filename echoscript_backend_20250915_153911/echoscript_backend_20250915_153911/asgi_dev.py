import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

# ASR
from faster_whisper import WhisperModel
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, Text, create_engine, select
from sqlalchemy import text as sqla_text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ---------- config ----------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALLOW_ORIGINS = [o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",")]

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "data")).resolve()
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL_SIZE", "small"
)  # tiny/base/small/medium/large-v3/distil-large-v3/turbo
ENV_DEVICE = os.getenv("WHISPER_DEVICE")  # force device if set
ENV_COMPUTE = os.getenv("WHISPER_COMPUTE")  # force compute if set

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- models ----------
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(String, nullable=False, server_default="free")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqla_text("now()")
    )


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="queued")
    transcript = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqla_text("now()")
    )


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


def create_access_token(
    sub: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def pick_device_and_compute() -> tuple[str, str]:
    # Respect explicit env overrides first
    if ENV_DEVICE:
        return ENV_DEVICE, (
            ENV_COMPUTE or ("float16" if ENV_DEVICE == "cuda" else "int8")
        )
    # Auto-pick: CUDA if CTranslate2 sees GPUs, else CPU
    try:
        import ctranslate2 as ct2

        if getattr(ct2, "get_cuda_device_count", lambda: 0)() > 0:
            return "cuda", "float16"  # fastest/accurate on GPU
    except Exception:
        pass
    return "cpu", "int8"  # fastest sensible default on CPU


def has_onnxruntime() -> bool:
    try:
        import onnxruntime  # noqa: F401

        return True
    except Exception:
        return False


# ---------- app ----------
app = FastAPI(title="EchoScript API", version="0.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ORIGINS == ["*"] else ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WHISPER: WhisperModel | None = None
VAD_ENABLED: bool = False
DEVICE: str = "cpu"
COMPUTE: str = "int8"


@app.on_event("startup")
def on_startup():
    global WHISPER, VAD_ENABLED, DEVICE, COMPUTE
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    DEVICE, COMPUTE = pick_device_and_compute()
    VAD_ENABLED = has_onnxruntime()  # only enable if ORT imports

    # Model loads automatically from HF Hub on first use
    WHISPER = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type=ENV_COMPUTE or COMPUTE,
    )


@app.get("/healthz")
def healthz():
    with engine.connect() as conn:
        conn.execute(sqla_text("select 1"))
    if WHISPER is None:
        raise HTTPException(status_code=500, detail="whisper_not_loaded")
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": ENV_COMPUTE or COMPUTE,
        "vad": VAD_ENABLED,
    }


@app.get("/__whoami")
def whoami():
    return {"file": __file__, "version": app.version}


@app.post("/api/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    row = (
        db.execute(select(User).where(User.email == form_data.username.lower()))
        .scalars()
        .first()
    )
    if not row or not verify_password(form_data.password, row.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )
    return Token(access_token=create_access_token(sub=row.id))


# ---------- transcription ----------
def _transcribe_file(audio_path: Path, language: str | None = "en") -> str:
    assert WHISPER is not None, "Whisper model not loaded"
    # Faster-Whisper decodes with PyAV (bundled FFmpeg) -> accepts most media containers
    # Use beam search for accuracy; enable VAD only if ORT is present
    segments, info = WHISPER.transcribe(
        str(audio_path),
        beam_size=5,
        best_of=1,
        vad_filter=VAD_ENABLED,
        language=language,  # force if you know it; else None for auto
        temperature=0.0,
        condition_on_previous_text=True,
    )
    parts: list[str] = [
        seg.text.strip() for seg in segments if getattr(seg, "text", "").strip()
    ]
    return (" ".join(parts)).strip() or "(empty transcript)"


@app.post("/api/v1/transcribe", response_model=JobOut)
async def transcribe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    language: str | None = "en",
):
    ext = Path(file.filename).suffix.lower() or ".bin"
    job_id = str(uuid.uuid4())
    target = STORAGE_DIR / f"{job_id}{ext}"

    # stream to disk to support large files without memory spikes
    with target.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    db.add(Job(id=job_id, filename=target.name, status="processing", transcript=None))
    db.commit()

    try:
        text = _transcribe_file(target, language=language)
        db.execute(
            sqla_text("UPDATE jobs SET status=:s, transcript=:t WHERE id=:i"),
            {"s": "done", "t": text, "i": job_id},
        )
        db.commit()
        return JobOut(
            job_id=job_id, status="done", filename=target.name, transcript=text
        )
    except Exception as e:
        import logging

        logging.exception(f"transcription_failed for job {job_id}")
        db.execute(
            sqla_text("UPDATE jobs SET status=:s, transcript=:t WHERE id=:i"),
            {"s": "error", "t": f"transcription_error: {e}", "i": job_id},
        )
        db.commit()
        return JSONResponse(
            status_code=500,
            content={
                "detail": "transcription_failed",
                "job_id": job_id,
                "error": str(e),
            },
        )


@app.get("/api/v1/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    row = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="job_not_found")
    return JobOut(
        job_id=row.id,
        status=row.status,
        filename=row.filename,
        transcript=row.transcript,
    )
