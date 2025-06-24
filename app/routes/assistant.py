#from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from uuid import uuid4
import openai
import os
from app.utils.logger import logger

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

# --- Environment ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- In-memory session context (replace with Redis soon) ---
user_memory: Dict[str, List[str]] = {}

# === Request Models ===

class AssistantQuery(BaseModel):
    transcript: str = Field(..., description="Full transcript content")
    question: str = Field(..., description="User’s query")
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

# === Intent Mapping ===

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

# === Mode Classifier ===

def classify_mode(transcript: str, question: str) -> str:
    prompt = f"""
Classify the user's goal based on the transcript and question.
Choose only one: summarize, clarify, actions, insight, explain, compare, next_steps, casual_chat

Transcript: {transcript[:1000]}
Question: {question}
""".strip()

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        mode = res.choices[0].message["content"].strip().split()[0].lower()
        return mode if mode in INTENT_MAP else "auto"
    except Exception as e:
        logger.warning(f"[Mode Classifier] fallback to 'auto': {e}")
        return "auto"

# === Prompt Builder ===

def build_prompt(data: AssistantQuery) -> tuple[list, str]:
    tone = data.tone or "friendly"
    voice = data.voice or "expert"
    mode = data.mode if data.mode != "auto" else classify_mode(data.transcript, data.question)

    system_msg = (
        f"You are EchoScript.AI — an adaptive AI assistant.\n"
        f"Use a {tone} tone and speak with {voice} style.\n"
        f"{INTENT_MAP.get(mode, 'Be helpful and context-aware.')}"
    )

    messages = [{"role": "system", "content": system_msg}]

    # Memory + prior interactions
    memory = user_memory.get(data.user_id, [])[-3:]
    for line in memory + data.history[-3:]:
        messages.append({"role": "user", "content": line})

    # Current query
    messages.append({
        "role": "user",
        "content": f"Transcript:\n{data.transcript[:4000]}\n\nQuestion:\n{data.question}"
    })

    return messages, mode

# === Smart Assistant Entry Point ===

@router.post("/ask", response_model=AssistantResponse)
async def ask_smart_assistant(data: AssistantQuery):
    try:
        messages, mode = build_prompt(data)

        try:
            # Try GPT-4 first
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.65,
                max_tokens=1400,
            )
        except Exception as e:
            logger.warning(f"[Assistant] GPT-4 failed, fallback to 3.5: {e}")
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.65,
                max_tokens=1400,
            )

        reply = res.choices[0].message["content"].strip()

        # Save memory
        user_memory.setdefault(data.user_id, []).append(data.question)
        if len(user_memory[data.user_id]) > 10:
            user_memory[data.user_id] = user_memory[data.user_id][-10:]

        return AssistantResponse(response=reply, mode=mode)

    except Exception as e:
        logger.error(f"[Assistant] Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Assistant failed to respond.")

# === Feedback Training Route ===

@router.post("/train", response_model=dict)
async def train_assistant(example: TrainingExample):
    if not example.user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    feedback = (
        f"[TRAINING] Instruction: {example.instruction} | Correction: {example.correction or 'N/A'} | "
        f"Rating: {example.rating or 'N/A'} | Bad Reply: {example.bad_reply or 'None'}"
    )

    user_memory.setdefault(example.user_id, []).append(feedback)

    logger.info(f"[Feedback] Stored training input for {example.user_id}")
    return {"message": "Feedback stored.", "data": feedback}
