"""
Live Groq connectivity checks (uses GROQ_API_KEY from .env — never log the key).

Run from repo root: python -m pytest tests/test_groq_live.py -v
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase2.preferences import UserPreferences
from zomato_recommendation.phase3.groq_client import call_groq_chat
from zomato_recommendation.phase3.recommend import recommend_with_groq
from zomato_recommendation.phase3.settings import GroqSettings, get_groq_settings


def _require_groq_key() -> GroqSettings:
    get_groq_settings.cache_clear()
    s = GroqSettings()
    if not (s.groq_api_key and s.groq_api_key.strip()):
        pytest.skip("GROQ_API_KEY missing or empty in .env")
    return s


def test_groq_api_key_loaded_from_env():
    """Settings load a non-trivial API key (value is never printed)."""
    s = _require_groq_key()
    assert len(s.groq_api_key.strip()) >= 8
    assert s.groq_model.strip() != ""


def test_groq_client_minimal_json_response():
    """Groq returns non-empty JSON for a trivial prompt."""
    settings = _require_groq_key()
    messages = [
        {
            "role": "system",
            "content": 'Reply with JSON only: {"status":"ok","test":"groq_live"}',
        },
        {"role": "user", "content": "Ping."},
    ]
    raw = call_groq_chat(messages, settings=settings)
    data = json.loads(raw)
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


def test_recommend_with_groq_one_candidate():
    """End-to-end Phase 3 call with a single synthetic candidate."""
    settings = _require_groq_key()
    df = pd.DataFrame(
        [
            {
                M.COL_ID: "live_test_001",
                M.COL_NAME: "Integration Test Bistro",
                M.COL_CITY: "Bangalore",
                M.COL_LOCATION: "Indiranagar",
                M.COL_CUISINES: "Italian, Continental",
                M.COL_RATING: 4.3,
                M.COL_COST_FOR_TWO: 950.0,
                M.COL_RAW_FEATURES: "Outdoor seating, good for families.",
                M.COL_VOTES: 42,
                M.COL_SOURCE_INDEX: 0,
            }
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget_max_inr=1500.0,
        cuisine="Italian",
        min_rating=4.0,
        extras="family-friendly",
    )
    out = recommend_with_groq(
        df,
        prefs,
        top_n=1,
        constraints_relaxed=False,
        settings=settings,
    )
    assert out.degraded is False
    assert len(out.recommendations) == 1
    r = out.recommendations[0]
    assert r.name == "Integration Test Bistro"
    assert r.cuisine == "Italian, Continental"
    assert r.rating == pytest.approx(4.3)
    assert "₹" in r.estimated_cost or r.estimated_cost == "Unknown"
    assert len(r.explanation.strip()) >= 20
    assert out.meta.model == settings.groq_model
