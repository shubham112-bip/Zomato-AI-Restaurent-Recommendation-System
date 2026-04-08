"""Phase 3 — Groq LLM: prompts, JSON parse, merge (architecture §5.3–5.4)."""

from zomato_recommendation.phase3.recommend import recommend_with_groq
from zomato_recommendation.phase3.schemas import (
    PROMPT_VERSION,
    GroqRecommendationResult,
    RecommendationMeta,
    RestaurantRecommendation,
)
from zomato_recommendation.phase3.settings import GroqSettings, get_groq_settings

__all__ = [
    "PROMPT_VERSION",
    "GroqRecommendationResult",
    "GroqSettings",
    "RecommendationMeta",
    "RestaurantRecommendation",
    "get_groq_settings",
    "recommend_with_groq",
]
