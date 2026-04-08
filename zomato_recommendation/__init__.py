"""Zomato-style restaurant recommendation package (phase-organized modules under ``phase0``–``phase5``)."""

from zomato_recommendation.phase1 import load_restaurants
from zomato_recommendation.phase2 import UserPreferences, select_candidates
from zomato_recommendation.phase3 import GroqRecommendationResult, recommend_with_groq

# Phase 4 API: ``from zomato_recommendation.phase4 import app`` (keeps root import lightweight).

__all__ = [
    "GroqRecommendationResult",
    "load_restaurants",
    "recommend_with_groq",
    "select_candidates",
    "UserPreferences",
]
