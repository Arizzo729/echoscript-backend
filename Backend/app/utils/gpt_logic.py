# app/utils/gpt_logic.py

import json
from json import JSONDecodeError
from typing import Any, List

import openai
from openai import OpenAIError

from app.config import config
from app.utils.logger import logger

# Alias ChatCompletion dynamically so MyPy sees it defined
ChatCompletion: Any = openai.ChatCompletion  # type: ignore[attr-defined]

# Initialize OpenAI API key
openai.api_key = config.OPENAI_API_KEY


def summarize_transcript(
    text: str,
    model: str = "gpt-4",
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """
    Generate a concise summary of the provided transcript text.
    """
    system_prompt = "You are a helpful assistant that summarizes transcripts into concise, accurate overviews."
    user_prompt = (
        f"Please provide a concise summary for the following transcript:\n\n{text}"
    )

    try:
        response = ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error during summary: {e}")
        raise

    return response.choices[0].message.content.strip()


def analyze_sentiment(
    text: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 50,
) -> str:
    """
    Analyze the sentiment of the transcript text.
    """
    system_prompt = (
        "You are an analytical assistant that determines sentiment of provided text. "
        "Respond with one word: Positive, Neutral, or Negative."
    )
    user_prompt = f"Transcript text:\n\n{text}"

    try:
        response = ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error during sentiment analysis: {e}")
        raise

    return response.choices[0].message.content.strip()


def extract_keywords(
    text: str,
    num_keywords: int = 5,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 100,
) -> List[str]:
    """
    Extract the top keywords or key phrases from the transcript text.
    """
    system_prompt = (
        "You are an assistant that extracts the most important keywords or phrases from the given text. "
        "Return only a JSON array of keywords."
    )
    user_prompt = (
        f"Extract the top {num_keywords} keywords or key phrases "
        f"from the following transcript:\n\n{text}"
    )

    try:
        response = ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error during keyword extraction: {e}")
        raise

    content = response.choices[0].message.content.strip()

    # Try parsing JSON array of keywords
    try:
        keywords = json.loads(content)
        if isinstance(keywords, list):
            return [str(k).strip() for k in keywords]
    except JSONDecodeError as e:
        logger.warning(f"Could not parse keywords JSON: {e}")

    # Fallback: split by commas
    return [k.strip() for k in content.split(",")][:num_keywords]


def translate_text(
    text: str,
    target_language: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str:
    """
    Translate the transcript text into the target language.
    """
    system_prompt = (
        f"You are a translation assistant. Translate the provided text into {target_language}. "
        "Maintain the original meaning and formatting."
    )
    user_prompt = f"Translate the following text:\n\n{text}"

    try:
        response = ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error during translation: {e}")
        raise

    return response.choices[0].message.content.strip()


def clean_transcript(
    text: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str:
    """
    Clean and polish the transcript text.
    """
    system_prompt = (
        "You are a helpful assistant that cleans and polishes raw transcript text. "
        "Remove filler words, correct grammar and punctuation, and produce clear readable text."
    )
    user_prompt = f"Clean the following transcript text:\n\n{text}"

    try:
        response = ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error during cleaning: {e}")
        raise

    return response.choices[0].message.content.strip()


__all__ = [
    "summarize_transcript",
    "analyze_sentiment",
    "extract_keywords",
    "translate_text",
    "clean_transcript",
]
