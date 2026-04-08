"""Groq Cloud API call (architecture §5.3)."""

from __future__ import annotations

import logging

from groq import Groq

from zomato_recommendation.phase3.settings import GroqSettings

logger = logging.getLogger(__name__)


def call_groq_chat(
    messages: list[dict[str, str]],
    *,
    settings: GroqSettings,
) -> str:
    """
    Run chat completions against Groq. Requires ``GROQ_API_KEY``.

    Uses ``json_object`` response format when the API accepts it; falls back without on error.
    """
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set (use .env or environment).")

    client = Groq(api_key=settings.groq_api_key)
    kwargs = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.35,
    }
    try:
        completion = client.chat.completions.create(
            **kwargs,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        logger.warning("Groq json_object mode failed (%s); retrying without it.", e)
        completion = client.chat.completions.create(**kwargs)

    choice = completion.choices[0].message
    text = (choice.content or "").strip()
    if not text:
        raise RuntimeError("Empty completion from Groq")
    return text
