"""Phase 2: filtering, relaxation, top-K (no LLM, no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from zomato_recommendation.filtering.selection import select_candidates
from zomato_recommendation.ingestion import field_mapping as M
from zomato_recommendation.preferences import UserPreferences


def _row(
    *,
    rid: str,
    name: str,
    city: str,
    location: str,
    cuisines: str,
    rating: float | None,
    cost: float | None,
    votes: int,
    raw: str = "",
) -> dict:
    return {
        M.COL_ID: rid,
        M.COL_NAME: name,
        M.COL_CITY: city,
        M.COL_LOCATION: location,
        M.COL_CUISINES: cuisines,
        M.COL_RATING: rating,
        M.COL_COST_FOR_TWO: cost,
        M.COL_RAW_FEATURES: raw,
        M.COL_VOTES: votes,
        M.COL_SOURCE_INDEX: 0,
    }


def test_select_candidates_empty_input():
    empty = pd.DataFrame(columns=list(M.CANONICAL_COLUMNS))
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=3.0,
    )
    out = select_candidates(empty, prefs, top_k=10, k_min=1)
    assert len(out.candidates) == 0
    assert out.constraints_relaxed is False


def test_select_candidates_no_match_location():
    df = pd.DataFrame(
        [
            _row(
                rid="a",
                name="R1",
                city="Mumbai",
                location="Andheri",
                cuisines="Chinese",
                rating=4.5,
                cost=800.0,
                votes=10,
            )
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=3.0,
    )
    out = select_candidates(df, prefs, top_k=10, k_min=1)
    assert len(out.candidates) == 0
    assert out.relaxation_steps  # widened / budget / etc. until exhausted


def test_select_candidates_sorts_by_rating_then_votes():
    df = pd.DataFrame(
        [
            _row(
                rid="low",
                name="A",
                city="Bangalore",
                location="Indiranagar",
                cuisines="Chinese",
                rating=4.0,
                cost=900.0,
                votes=100,
            ),
            _row(
                rid="high",
                name="B",
                city="Bangalore",
                location="Koramangala",
                cuisines="Chinese",
                rating=4.5,
                cost=900.0,
                votes=1,
            ),
            _row(
                rid="tie",
                name="C",
                city="Bangalore",
                location="Jayanagar",
                cuisines="Chinese",
                rating=4.5,
                cost=900.0,
                votes=50,
            ),
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=3.0,
    )
    out = select_candidates(df, prefs, top_k=10, k_min=1)
    ids = out.candidates[M.COL_ID].tolist()
    # 4.5 first; tie 4.5: higher votes before lower (tie-breaker: C then B)
    assert ids[0] == "tie"
    assert ids[1] == "high"
    assert ids[2] == "low"


def test_top_k_limits_rows():
    rows = [
        _row(
            rid=f"r{i}",
            name=f"N{i}",
            city="Bangalore",
            location="x",
            cuisines="Thai",
            rating=4.0,
            cost=800.0,
            votes=i,
        )
        for i in range(50)
    ]
    df = pd.DataFrame(rows)
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Thai",
        min_rating=3.0,
    )
    out = select_candidates(df, prefs, top_k=7, k_min=1)
    assert len(out.candidates) == 7


def test_location_widening_bengaluru_to_bangalore():
    df = pd.DataFrame(
        [
            _row(
                rid="x",
                name="South",
                city="Bangalore",
                location="HSR",
                cuisines="Cafe",
                rating=4.2,
                cost=600.0,
                votes=5,
            )
        ]
    )
    prefs = UserPreferences(
        location="Bengaluru",
        budget="low",
        cuisine="Cafe",
        min_rating=4.0,
    )
    out = select_candidates(df, prefs, top_k=5, k_min=1)
    assert len(out.candidates) == 1
    assert any("widen_location" in s for s in out.relaxation_steps)


def test_secondary_cuisine_dropped_on_relax():
    df = pd.DataFrame(
        [
            _row(
                rid="ok",
                name="Only Chinese",
                city="Bangalore",
                location="a",
                cuisines="Chinese",
                rating=4.0,
                cost=800.0,
                votes=1,
            ),
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Chinese",
        min_rating=4.0,
        secondary_cuisines=["Thai"],
    )
    out = select_candidates(df, prefs, top_k=5, k_min=5)
    assert len(out.candidates) == 1
    assert any("secondary" in s for s in out.relaxation_steps)


def test_extras_boost_prefers_keyword_in_raw_features():
    df = pd.DataFrame(
        [
            _row(
                rid="no",
                name="A",
                city="Bangalore",
                location="a",
                cuisines="Italian",
                rating=4.5,
                cost=900.0,
                votes=0,
                raw="quiet dinner",
            ),
            _row(
                rid="yes",
                name="B",
                city="Bangalore",
                location="b",
                cuisines="Italian",
                rating=4.5,
                cost=900.0,
                votes=0,
                raw="family-friendly place with kids menu",
            ),
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        extras="family-friendly",
    )
    out = select_candidates(df, prefs, top_k=2, k_min=1)
    assert out.candidates[M.COL_ID].iloc[0] == "yes"


def test_custom_budget_json(tmp_path: Path):
    path = tmp_path / "bands.json"
    path.write_text(
        json.dumps(
            {
                "bands": {
                    "low": {"min": 0, "max": 100},
                    "medium": {"min": 100, "max": 300},
                    "high": {"min": 300, "max": 10000},
                }
            }
        ),
        encoding="utf-8",
    )
    df = pd.DataFrame(
        [
            _row(
                rid="1",
                name="Cheap",
                city="Bangalore",
                location="a",
                cuisines="X",
                rating=4.0,
                cost=50.0,
                votes=1,
            ),
            _row(
                rid="2",
                name="Pricey",
                city="Bangalore",
                location="b",
                cuisines="X",
                rating=4.5,
                cost=500.0,
                votes=1,
            ),
        ]
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget="low",
        cuisine="X",
        min_rating=3.0,
    )
    out = select_candidates(df, prefs, top_k=5, k_min=1, budget_bands_path=path)
    ids = set(out.candidates[M.COL_ID].tolist())
    assert ids == {"1"}
