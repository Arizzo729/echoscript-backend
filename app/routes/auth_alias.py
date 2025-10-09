# app/routes/auth_alias.py
"""
Provides /auth/signin as a stable alias that redirects to /auth/login.
Mounted under /api and /v1, so the final paths are:
- /api/auth/signin  ->  /api/auth/login
- /v1/auth/signin   ->  /api/auth/login  (we purposely unify on /api)
"""
from fastapi import APIRouter
from starlette.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signin")
async def signin_alias():
    # 307 keeps method/body; fetch follows by default
    return RedirectResponse(url="/api/auth/login", status_code=307)
