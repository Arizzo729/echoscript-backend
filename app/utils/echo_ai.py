# app/utils/echo_ai.py — EchoScript.AI GPT Enhancement Module

import os
import openai
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")

openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are a professional transcription assistant. "
    "Your job is to enhance transcripts generated from real human speech. "
    "Polish grammar, fix punctuation, remove filler words when appropriate, "
    "but do not hallucinate or change factual meaning. Respond in plain text only."
)

async def apply_gpt_cleanup(text: str, language: str = "en") -> str:
    """
    Enhance transcript clarity and formatting using OpenAI GPT.
    
    Args:
        text (str): Raw transcript text.
        language (str): Optional hint for language, default is English.
    
    Returns:
        str: Cleaned and human-readable transcript.
    """
    if not text.strip():
        return ""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Clean and format this transcript in {language}:\n\n{text}"}
            ],
            temperature=0.4,
            max_tokens=3000,
            n=1,
        )
        cleaned = response["choices"][0]["message"]["content"].strip()
        return cleaned or text

    except openai.error.OpenAIError as e:
        # Log or handle OpenAI API-specific failures gracefully
        print(f"[GPT Cleanup Error] OpenAI API failed: {e}")
        return text

    except Exception as e:
        # Catch-all for unexpected issues
        print(f"[GPT Cleanup Error] Unexpected error: {e}")
        return text
