# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EchoScript API", version="1.0.0")

# --- CORS: allow your frontend(s) ---
ALLOWED_ORIGINS = [
    "https://echoscript.ai",
    "https://www.echoscript.ai",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# allow extra origins via env if needed (comma-separated)
extra = os.getenv("ALLOW_ORIGINS", "")
if extra:
    ALLOWED_ORIGINS += [o.strip() for o in extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(ALLOWED_ORIGINS)),  # de-dup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "env": os.getenv("ENV", "production")}

# --- Router includes (no prefixes here on purpose) ---
# We include routers "as-is" so whatever prefixes you defined inside each file just work.
def _try_include(module_path: str, attr: str = "router"):
    try:
        mod = __import__(module_path, fromlist=[attr])
        router = getattr(mod, attr, None)
        if router is not None:
            app.include_router(router)  # no extra prefix here
            return True
    except Exception:
        pass
    return False

# Common router modules you’ve shown in screenshots / uploads:
_try_include("app.routes.health")              # e.g. @router.get("/healthz")
_try_include("app.routes.signup")              # may have prefix="/api/auth" inside
_try_include("app.routes.auth")                # may have /login etc.
_try_include("app.routes.stripe_checkout")     # may have prefix="/api/stripe" inside
_try_include("app.routes.stripe_webhook")      # webhook under /api/stripe
_try_include("app.routes.transcribe")          # /api/transcribe or similar

# If you also keep some in app.<file> (not in routes/), try those as well:
_try_include("app.health")
_try_include("app.signup")
_try_include("app.auth")
_try_include("app.stripe_checkout")
_try_include("app.stripe_webhook")
_try_include("app.transcribe")

# Root (optional)
@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-backend"}

