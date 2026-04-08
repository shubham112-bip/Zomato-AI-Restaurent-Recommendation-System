"""Phase 4 API tests (no Hugging Face download; Groq mocked)."""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase3.schemas import (
    PROMPT_VERSION,
    GroqRecommendationResult,
    RecommendationMeta,
    RestaurantRecommendation,
)
from zomato_recommendation.phase4.app import app


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                M.COL_ID: "api_t1",
                M.COL_NAME: "Pasta House",
                M.COL_CITY: "Bangalore",
                M.COL_LOCATION: "Koramangala",
                M.COL_CUISINES: "Italian",
                M.COL_RATING: 4.4,
                M.COL_COST_FOR_TWO: 900.0,
                M.COL_RAW_FEATURES: "Cozy, family-friendly.",
                M.COL_VOTES: 50,
                M.COL_SOURCE_INDEX: 0,
            },
            {
                M.COL_ID: "api_t2",
                M.COL_NAME: "Spice Route",
                M.COL_CITY: "Bangalore",
                M.COL_LOCATION: "Indiranagar",
                M.COL_CUISINES: "Indian, Italian",
                M.COL_RATING: 4.1,
                M.COL_COST_FOR_TWO: 1200.0,
                M.COL_RAW_FEATURES: "Quick service.",
                M.COL_VOTES: 30,
                M.COL_SOURCE_INDEX: 1,
            },
        ]
    )


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ZOMATO_SKIP_DATASET_LOAD", "1")
    # Re-import to pick up env if module already loaded — app already created
    with TestClient(app) as client:
        app.state.df = _sample_df()
        yield client


def test_health(api_client: TestClient):
    r = api_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "dataset_ready" in data
    assert data["dataset_ready"] is True


def test_ui_root_returns_api_metadata(api_client: TestClient):
    r = api_client.get("/")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/json")
    data = r.json()
    assert data.get("service") == "zomato-recommendation-api"
    assert "docs" in data


def test_get_locations(api_client: TestClient):
    r = api_client.get("/api/v1/locations")
    assert r.status_code == 200
    data = r.json()
    assert "locations" in data
    locs = data["locations"]
    assert "Bangalore" in locs
    assert "Koramangala" in locs
    assert "Indiranagar" in locs


def test_get_cuisines(api_client: TestClient):
    r = api_client.get("/api/v1/cuisines")
    assert r.status_code == 200
    data = r.json()
    assert "cuisines" in data
    assert "Italian" in data["cuisines"]
    assert "Indian" in data["cuisines"]


def test_post_recommendations_unknown_cuisine_422(api_client: TestClient):
    r = api_client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "cuisine": "NotARealCuisineLabelXyz123",
            "budget_max_inr": 2000.0,
            "min_rating": 4.0,
        },
    )
    assert r.status_code == 422


def test_post_recommendations_validation_error(api_client: TestClient):
    """Invalid body (e.g. min_rating > 5) → 422."""
    r = api_client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget_max_inr": 1500.0,
            "cuisine": "Italian",
            "min_rating": 9.0,
        },
    )
    assert r.status_code == 422


def test_post_recommendations_200_mocked_groq(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def fake_groq(*args, **kwargs):
        return GroqRecommendationResult(
            summary="Mock summary.",
            recommendations=[
                RestaurantRecommendation(
                    name="Pasta House",
                    cuisine="Italian",
                    rating=4.4,
                    estimated_cost="₹900",
                    explanation="Strong Italian match for your preferences.",
                    rank=1,
                )
            ],
            meta=RecommendationMeta(
                candidates_considered=2,
                constraints_relaxed=False,
                model="mock-model",
                prompt_version=PROMPT_VERSION,
            ),
            degraded=False,
        )

    monkeypatch.setattr(
        "zomato_recommendation.phase4.service.recommend_with_groq",
        fake_groq,
    )

    r = api_client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget_max_inr": 2000.0,
            "cuisine": "Italian",
            "min_rating": 4.0,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["summary"] == "Mock summary."
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["name"] == "Pasta House"
    assert data["meta"]["candidates_considered"] == 2
    assert data["meta"]["prompt_version"] == PROMPT_VERSION
    assert data["meta"].get("cuisine_resolved") in (None, "Italian")
    assert data["degraded"] is False


def test_post_location_only_passes_shortlist_top_n_to_groq(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, int] = {}

    def fake_groq(candidates, prefs, *, top_n: int, **kwargs):
        captured["top_n"] = top_n
        return GroqRecommendationResult(
            summary="All.",
            recommendations=[
                RestaurantRecommendation(
                    name="Pasta House",
                    cuisine="Italian",
                    rating=4.4,
                    estimated_cost="₹900",
                    explanation="One.",
                    rank=1,
                ),
                RestaurantRecommendation(
                    name="Spice Route",
                    cuisine="Indian, Italian",
                    rating=4.1,
                    estimated_cost="₹1200",
                    explanation="Two.",
                    rank=2,
                ),
            ],
            meta=RecommendationMeta(
                candidates_considered=2,
                constraints_relaxed=False,
                model="mock-model",
                prompt_version=PROMPT_VERSION,
            ),
            degraded=False,
        )

    monkeypatch.setattr(
        "zomato_recommendation.phase4.service.recommend_with_groq",
        fake_groq,
    )

    r = api_client.post(
        "/v1/recommendations",
        json={"location": "Bangalore"},
    )
    assert r.status_code == 200
    assert captured.get("top_n") == 2
    data = r.json()
    assert len(data["recommendations"]) == 2


def test_post_recommendations_typo_sets_cuisine_resolved(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def fake_groq(*args, **kwargs):
        return GroqRecommendationResult(
            summary="Ok.",
            recommendations=[
                RestaurantRecommendation(
                    name="Pasta House",
                    cuisine="Italian",
                    rating=4.4,
                    estimated_cost="₹900",
                    explanation="Ok.",
                    rank=1,
                )
            ],
            meta=RecommendationMeta(
                candidates_considered=1,
                constraints_relaxed=False,
                model="mock-model",
                prompt_version=PROMPT_VERSION,
            ),
            degraded=False,
        )

    monkeypatch.setattr(
        "zomato_recommendation.phase4.service.recommend_with_groq",
        fake_groq,
    )

    r = api_client.post(
        "/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget_max_inr": 2000.0,
            "cuisine": "Italin",
            "min_rating": 4.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["meta"]["cuisine_resolved"] == "Italian"


def test_post_api_v1_recommendations_same_as_legacy(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def fake_groq(*args, **kwargs):
        return GroqRecommendationResult(
            summary="Mock summary.",
            recommendations=[
                RestaurantRecommendation(
                    name="Pasta House",
                    cuisine="Italian",
                    rating=4.4,
                    estimated_cost="₹900",
                    explanation="Strong Italian match for your preferences.",
                    rank=1,
                )
            ],
            meta=RecommendationMeta(
                candidates_considered=2,
                constraints_relaxed=False,
                model="mock-model",
                prompt_version=PROMPT_VERSION,
            ),
            degraded=False,
        )

    monkeypatch.setattr(
        "zomato_recommendation.phase4.service.recommend_with_groq",
        fake_groq,
    )

    r = api_client.post(
        "/api/v1/recommendations",
        json={
            "location": "Bangalore",
            "budget_max_inr": 2000.0,
            "cuisine": "Italian",
            "min_rating": 4.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["summary"] == "Mock summary."


def test_post_recommendations_empty_dataset_message(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ZOMATO_SKIP_DATASET_LOAD", "1")
    empty = pd.DataFrame(columns=list(M.CANONICAL_COLUMNS))
    with TestClient(app) as client:
        app.state.df = empty
        r = client.post(
            "/v1/recommendations",
            json={
                "location": "Bangalore",
                "budget_max_inr": 800.0,
                "cuisine": "Italian",
                "min_rating": 4.5,
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["recommendations"] == []
    assert body["message"] is not None
