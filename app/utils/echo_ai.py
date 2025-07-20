# ---- EchoScript.AI: echo_ai.py ----

import openai
import zlib
import hashlib
from typing import Literal
from app.config import Config
from app.utils.logger import logger

openai.api_key = Config.OPENAI_API_KEY

# === Preset Tones and Styles ===
TONE_STYLES = {
    "default": "Summarize the transcript clearly and intelligently.",
    "friendly": "Summarize the transcript in a friendly, human tone.",
    "formal": "Provide a professional summary suitable for reports.",
    "bullet": "Summarize using clear bullet points only.",
    "action": "Extract tasks, follow-ups, and decisions only.",
}

LENGTH_STYLES = {
    "short": "Use 1–2 short sentences max.",
    "medium": "Use 3–5 concise sentences for clarity.",
    "long": "Provide a rich, paragraph-style detailed summary.",
}


# === Truncate Long Inputs ===
def truncate(text: str, max_chars: int = 3900) -> str:
    return text[:max_chars] + "..." if len(text) > max_chars else text


# === Optional Hash (for caching, deduplication, etc) ===
def get_checksum(text: str) -> str:
    return hashlib.md5(zlib.compress(text.encode())).hexdigest()


# === Main GPT Enhancement Function ===
async def enhance_transcript(
    raw_text: str,
    task: Literal["summarize", "clarify", "filler", "label"] = "summarize",
    tone: Literal["default", "friendly", "formal", "bullet", "action"] = "default",
    length: Literal["short", "medium", "long"] = "medium"
) -> str:
    if not raw_text.strip():
        return "Transcript is empty."

    prompt_map = {
        "summarize": f"{TONE_STYLES[tone]} {LENGTH_STYLES[length]}",
        "clarify": "Rewrite this transcript to be more readable, well-structured, and grammatically correct.",
        "filler": "Remove filler words, hesitations, and false starts. Improve readability without changing meaning.",
        "label": "Label each speaker clearly. Use 'Speaker 1:', 'Speaker 2:', etc., based on natural breaks.",
    }

    system_prompt = "You are Echo AI, a smart assistant for transcribing and enhancing spoken audio content."
    user_prompt = prompt_map.get(task, TONE_STYLES["default"]) + "\n\n" + truncate(raw_text)

    logger.info(f"🔍 Enhancing transcript [{task}] | tone={tone}, length={length}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ AI Enhancement Failed: {str(e)}")
        return "Sorry, an error occurred while enhancing the transcript."


# === Simple Wrapper (legacy alias for cleanup) ===
async def apply_gpt_cleanup(text: str) -> str:
    """Legacy wrapper: clean up raw transcript with default clarity task."""
    return await enhance_transcript(
        raw_text=text,
        task="clarify",
        tone="default",
        length="medium"
    )
