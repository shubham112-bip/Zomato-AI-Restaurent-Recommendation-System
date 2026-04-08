"""Groq and prompt settings from environment (architecture §5.3, §8.1)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: zomato_recommendation/phase3/settings.py -> parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ENV = _REPO_ROOT / ".env"


class GroqSettings(BaseSettings):
    """Loads ``GROQ_API_KEY`` and ``GROQ_MODEL`` from ``.env`` / environment."""

    model_config = SettingsConfigDict(
        # Resolve .env from package location so tests/CI work regardless of CWD
        env_file=(str(_DEFAULT_ENV), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GROQ_API_KEY",
            "API_KEY",  # common shorthand in .env
            "groq_api_key",
        ),
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL", "groq_model"),
    )


@lru_cache
def get_groq_settings() -> GroqSettings:
    return GroqSettings()
