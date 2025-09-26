# app/main.py
import os

# 🔒 Force CPU everywhere (set env before any ML libs load)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # hide GPUs from PyTorch/others
os.environ.setdefault("ORT_DISABLE_GPU", "1")  # force onnxruntime CPU

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

IS_DEV = os.getenv("ENV", "development").lower() == "development"

app = FastAPI(
    title="EchoScriptAI API",
    version="0.1.0",
    servers=[{"url": "/"}],  # Swagger uses same-origin to avoid mixed origin issues
)

# --- CORS ---
if IS_DEV:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000",
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Routers ---
from app.routes import transcribe as transcribe_router

app.include_router(transcribe_router.router)
print(">> Transcribe routes loaded:", [r.path for r in transcribe_router.router.routes])

# Optional routers
try:
    from app.routes import auth as auth_router

    app.include_router(auth_router.router)
except Exception as e:
    print("Auth router not loaded:", e)

try:
    from app.routes import stripe_webhook as stripe_router

    app.include_router(stripe_router.router)
except Exception as e:
    print("Stripe router not loaded:", e)

# Dev override for auth
if IS_DEV:
    try:
        from app.dependencies import get_current_user

        def _dev_user_override():
            return {"id": "dev_user", "email": "dev@example.com", "role": "admin"}

        app.dependency_overrides[get_current_user] = _dev_user_override
        print(">> DEV MODE: get_current_user is overridden (no JWT required).")
    except Exception as e:
        print("Dev override not applied:", e)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}
