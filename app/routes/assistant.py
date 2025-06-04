# ---- EchoScript.AI Backend: routes/assistant.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from uuid import uuid4
import openai
import os
from app.utils.logger import logger

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---- In-Memory User Context ----
user_memory = {}

# ---- Data Models ----
class AssistantQuery(BaseModel):
    transcript: str = Field(..., description="Full transcript context")
    question: str = Field(..., description="User's query")
    history: List[str] = Field(default_factory=list)
    user_id: str = "default"
    mode: Optional[str] = "auto"
    tone: Optional[Literal["friendly", "formal", "neutral"]] = "friendly"
    voice: Optional[Literal["expert", "teacher", "casual", "technical"]] = "expert"

class AssistantResponse(BaseModel):
    response: str
    mode: str

class TrainingExample(BaseModel):
    user_id: str
    instruction: str
    example_answer: str
    rating: Optional[int] = None
    correction: Optional[str] = None
    bad_reply: Optional[str] = None

# ---- Mode Classifier (GPT-3.5) ----
def classify_mode(transcript: str, question: str) -> str:
    prompt = f"""
Classify the user's goal based on the transcript and question.
Choose only one from: summarize, clarify, actions, insight, explain, compare, next_steps, casual_chat

Transcript: {transcript[:1000]}
Question: {question}
""".strip()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        mode = response.choices[0].message["content"].strip().lower().split()[0]
        return mode if mode in INTENT_MAP else "auto"
    except Exception as e:
        logger.warning(f"Mode classification fallback: {e}")
        return "auto"

# ---- Mode Prompts ----
INTENT_MAP = {
    "summarize": "Summarize the key points clearly.",
    "clarify": "Clarify unclear sections in plain English.",
    "actions": "List next steps and tasks.",
    "insight": "Reveal deeper meaning or implications.",
    "explain": "Explain concepts as if teaching.",
    "compare": "Compare themes or speakers.",
    "next_steps": "Suggest logical next steps.",
    "casual_chat": "Answer in a friendly, conversational way.",
}

# ---- Prompt Builder ----
def build_prompt(data: AssistantQuery) -> List[dict]:
    messages = []

    # Set tone and voice in system prompt
    tone = data.tone or "friendly"
    voice = data.voice or "expert"
    mode = data.mode if data.mode != "auto" else classify_mode(data.transcript, data.question)

    system_msg = f"You are EchoScript.AI — an adaptive AI assistant.\n"
    system_msg += f"Use a {tone} tone and speak with {voice} style.\n"
    system_msg += INTENT_MAP.get(mode, "Be helpful and context-aware.")

    messages.append({"role": "system", "content": system_msg})

    # Memory + History
    memory = user_memory.get(data.user_id, [])
    for prior in (memory[-3:] + data.history[-3:]):
        messages.append({"role": "user", "content": prior})

    # Main query
    messages.append({
        "role": "user",
        "content": f"Transcript:\n{data.transcript[:4000]}\n\nQuestion:\n{data.question}"
    })

    return messages, mode

# ---- Assistant Route ----
@router.post("/ask", response_model=AssistantResponse)
async def ask_smart_assistant(data: AssistantQuery):
    try:
        messages, mode = build_prompt(data)

        # Prefer GPT-4, fallback to 3.5
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.65,
                max_tokens=1400
            )
        except Exception as e:
            logger.warning(f"GPT-4 failed, retrying with GPT-3.5: {e}")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.65,
                max_tokens=1400
            )

        reply = response.choices[0].message["content"].strip()

        # Save memory
        user_memory.setdefault(data.user_id, []).append(data.question)
        if len(user_memory[data.user_id]) > 10:
            user_memory[data.user_id] = user_memory[data.user_id][-10:]

        return AssistantResponse(response=reply, mode=mode)

    except Exception as e:
        logger.error(f"Assistant error: {e}")
        raise HTTPException(status_code=500, detail="Assistant failed to respond.")

# ---- Feedback/Training Route ----
@router.post("/train", response_model=dict)
async def train_assistant(example: TrainingExample):
    if not example.user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    memory_entry = (
        f"[TRAINING] Instruction: {example.instruction} | Correction: {example.correction or 'N/A'} | "
        f"Rating: {example.rating or 'N/A'} | Bad Reply: {example.bad_reply or 'None'}"
    )
    user_memory.setdefault(example.user_id, []).append(memory_entry)

    logger.info(f"💡 Training feedback saved for {example.user_id}")
    return {"message": "Feedback stored.", "data": memory_entry}

