from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class AssistantQuery(BaseModel):
    prompt: str


class AssistantResponse(BaseModel):
    response: str


@router.post("", response_model=AssistantResponse)
async def ask_assistant(payload: AssistantQuery):
    # Minimal fake assistant used for tests; real implementation lives elsewhere.
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt required")
    return AssistantResponse(response=f"Echo: {payload.prompt}")
