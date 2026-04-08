"""Phase 3: Groq orchestration with mocked completions (no API key required)."""

from __future__ import annotations

import pandas as pd
import pytest

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase2.preferences import UserPreferences
from zomato_recommendation.phase3.merge import merge_llm_payload
from zomato_recommendation.phase3.parse import parse_llm_json
from zomato_recommendation.phase3.recommend import recommend_with_groq
from zomato_recommendation.phase3.schemas import LlmPayload, LlmRecommendationItem


def _one_candidate(*, rid: str = "rid1", name: str = "Test Cafe") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                M.COL_ID: rid,
                M.COL_NAME: name,
                M.COL_CITY: "Bangalore",
                M.COL_LOCATION: "Indiranagar",
                M.COL_CUISINES: "Italian",
                M.COL_RATING: 4.2,
                M.COL_COST_FOR_TWO: 900.0,
                M.COL_RAW_FEATURES: "family-friendly",
                M.COL_VOTES: 10,
                M.COL_SOURCE_INDEX: 0,
            }
        ]
    )


@pytest.fixture
def prefs() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget_max_inr=1500.0,
        cuisine="Italian",
        min_rating=4.0,
        extras="family-friendly",
    )


def test_parse_llm_json_plain():
    text = '{"summary": "Hi", "recommendations": [{"id": "a", "rank": 1, "explanation": "Because."}]}'
    p = parse_llm_json(text)
    assert p.summary == "Hi"
    assert len(p.recommendations) == 1
    assert p.recommendations[0].id == "a"


def test_parse_llm_json_fenced():
    text = '```json\n{"summary": null, "recommendations": []}\n```'
    p = parse_llm_json(text)
    assert p.recommendations == []


def test_recommend_with_groq_mock_success(prefs: UserPreferences):
    df = _one_candidate()

    def fake(*, messages, model: str) -> str:
        return (
            '{"summary": "Great pick.", "recommendations": ['
            '{"id": "rid1", "rank": 1, "explanation": "Matches Italian and area."}'
            "]}"
        )

    out = recommend_with_groq(
        df,
        prefs,
        top_n=3,
        completion_fn=fake,
        settings=None,
    )
    assert out.degraded is False
    assert out.summary == "Great pick."
    assert len(out.recommendations) == 1
    assert out.recommendations[0].name == "Test Cafe"
    assert out.recommendations[0].cuisine == "Italian"
    assert out.recommendations[0].rank == 1
    assert out.meta.prompt_version == "v1"
    assert out.meta.candidates_considered == 1


def test_recommend_with_groq_empty_candidates(prefs: UserPreferences):
    empty = pd.DataFrame(columns=list(M.CANONICAL_COLUMNS))
    out = recommend_with_groq(empty, prefs, completion_fn=lambda **kw: "{}")
    assert out.recommendations == []
    assert out.degraded is False


def test_recommend_fallback_on_bad_json(prefs: UserPreferences):
    df = _one_candidate()

    def bad(*, messages, model: str) -> str:
        return "not json"

    out = recommend_with_groq(df, prefs, top_n=2, completion_fn=bad)
    assert out.degraded is True
    assert len(out.recommendations) >= 1
    assert out.recommendations[0].name == "Test Cafe"


def test_recommend_fallback_unknown_ids(prefs: UserPreferences):
    df = _one_candidate()

    def wrong_id(*, messages, model: str) -> str:
        return (
            '{"summary": "x", "recommendations": ['
            '{"id": "nope", "rank": 1, "explanation": "bad"}]}'
        )

    out = recommend_with_groq(df, prefs, top_n=2, completion_fn=wrong_id)
    assert out.degraded is True
    assert out.recommendations[0].name == "Test Cafe"


def test_merge_llm_payload_dedupes_repeated_ids():
    df = _one_candidate()
    payload = LlmPayload(
        summary="x",
        recommendations=[
            LlmRecommendationItem(id="rid1", rank=1, explanation="first"),
            LlmRecommendationItem(id="rid1", rank=2, explanation="dup"),
        ],
    )
    out, _ = merge_llm_payload(payload, df, top_n=5)
    assert len(out) == 1
    assert out[0].explanation == "first"
