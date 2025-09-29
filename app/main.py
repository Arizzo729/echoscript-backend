@'
# app/main.py (minimal boot)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = os.getenv("GIT_SHA", "local")

def allowed():
    raw = os.getenv("API_ALLOWED_ORIGINS", "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

app = FastAPI(title="EchoScript API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-api", "version": APP_VERSION}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": APP_VERSION}
'@ | Set-Content app\main.py -Encoding UTF8
