# ---- EchoScript.AI: utils/gpt_logic.py ----

import openai
import asyncio
from typing import Literal
from app.config import Config
from app.utils.logger import logger

openai.api_key = Config.OPENAI_API_KEY

# ---- Presets ----
TONE_STYLES = {
    "default": "Summarize this transcript clearly and intelligently.",
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

# ---- Truncate Utility ----
def truncate(text: str, max_chars: int = 3900) -> str:
    return text[:max_chars] + "..." if len(text) > max_chars else text

# ---- Sync GPT Wrapper ----
def call_openai_sync(messages: list[dict], max_tokens=1000, temperature=0.4) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ OpenAI sync call failed: {e}")
        return "[OpenAI response failed.]"

# ---- Async GPT Wrapper ----
async def call_openai_async(messages: list[dict], max_tokens=2048, temperature=0.4) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ OpenAI async call failed: {e}")
        return "[OpenAI async response failed.]"

# ---- Summarization ----
def summarize_transcript(text: str, tone: str = "default", length: str = "medium") -> str:
    instruction = f"{TONE_STYLES.get(tone, TONE_STYLES['default'])} {LENGTH_STYLES.get(length, '')}".strip()

    prompt = f"""
{instruction}

Organize the summary using markdown:
## Main Topics
## Key Points
## Action Items
## Notable Quotes

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You are a brilliant summarizer of transcripts and conversations."},
        {"role": "user", "content": prompt},
    ]

    summary = call_openai_sync(messages, max_tokens=950)
    logger.info("✅ Summary generated.")
    return summary

# ---- Cleanup ----
def clean_transcript(text: str) -> str:
    prompt = f"""
Clean this transcript:
- Remove filler words like 'um', 'uh', 'like', etc.
- Fix grammar and punctuation
- Improve clarity and readability
- Retain speaker tone and intent

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You are an expert transcript editor improving clarity and flow."},
        {"role": "user", "content": prompt},
    ]

    cleaned = call_openai_sync(messages)
    logger.info("✅ Transcript cleaned.")
    return cleaned

# ---- Action Item Extraction ----
def extract_action_items(text: str) -> str:
    prompt = f"""
From this transcript, extract clear action items.
Each item should state:
- Who is responsible
- What needs to be done

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You're an assistant capturing follow-up tasks from meetings."},
        {"role": "user", "content": prompt},
    ]

    return call_openai_sync(messages, max_tokens=700)

# ---- Sentiment Analysis ----
def analyze_sentiment(text: str) -> str:
    prompt = f"""
Analyze the emotional tone and overall sentiment of this transcript.
Return one of: Positive, Neutral, or Negative, and explain briefly.

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You are a professional conversation tone analyst."},
        {"role": "user", "content": prompt},
    ]

    return call_openai_sync(messages, max_tokens=300, temperature=0.2)

# ---- Keyword Extraction ----
def extract_keywords(text: str, max_count: int = 10) -> str:
    prompt = f"""
Extract the top {max_count} keywords, named entities, or topics from the transcript.
Separate with commas. Avoid filler or generic words.

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You are a summarizer extracting keywords from text."},
        {"role": "user", "content": prompt},
    ]

    return call_openai_sync(messages, max_tokens=300)

# ---- Translation ----
async def translate_text(text: str, target_language: str = "en") -> str:
    prompt = f"""
Translate this transcript to {target_language}, preserving meaning and tone.

Transcript:
{truncate(text)}
""".strip()

    messages = [
        {"role": "system", "content": "You are an expert transcription editor and translator."},
        {"role": "user", "content": prompt},
    ]

    translated = await call_openai_async(messages)
    logger.info(f"✅ Transcript translated to {target_language}")
    return translated

