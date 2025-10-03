# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- import your routers ---
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.stripe_checkout import router as stripe_checkout_router
from app.routes.stripe_webhook import router as stripe_webhook_router

app = FastAPI(title="EchoScript API")

# Allow your frontend origins
ALLOWED_ORIGINS = [
    "https://echoscript.ai",
    "https://www.echoscript.ai",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],   # Authorization, Content-Type, etc.
)

# Mount routers (note: route files should use paths like "/signup", "/login", not "/api/...").
app.include_router(health_router)                                   # e.g. GET /healthz
app.include_router(auth_router,          prefix="/api/auth")        # POST /api/auth/signup, /login
app.include_router(stripe_checkout_router, prefix="/api/stripe")    # POST /api/stripe/create-checkout-session
app.include_router(stripe_webhook_router,  prefix="/api/stripe")    # POST /api/stripe/webhook

@app.get("/")
def root():
    return {"ok": True}

app.include_router(health_router, prefix="")

# These routers already set their own prefixes inside each file:
# - signup/login under /api/auth (your signup router defines prefix="/api/auth") :contentReference[oaicite:1]{index=1}
# - stripe checkout/webhooks under /api/stripe
app.include_router(signup_router)
try:
    app.include_router(auth_router)  # only if you actually have app/routes/auth.py
except Exception:
    # safe to ignore if you don't have a separate auth router
    pass
app.include_router(stripe_checkout_router)
app.include_router(stripe_webhook_router)

@app.get("/", tags=["Root"])
def root():
    return {"ok": True, "service": "echoscript-backend"}
