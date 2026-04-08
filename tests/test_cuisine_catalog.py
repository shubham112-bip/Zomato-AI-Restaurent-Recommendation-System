"""Cuisine catalog merge and fuzzy resolution."""

from __future__ import annotations

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase2.cuisine_catalog import (
    build_cuisine_catalog,
    resolve_primary_cuisine,
)


def test_build_cuisine_catalog_dataset_only_sorted():
    df = pd.DataFrame(
        [
            {
                M.COL_ID: "a",
                M.COL_NAME: "x",
                M.COL_CITY: "B",
                M.COL_LOCATION: "l",
                M.COL_CUISINES: "Italian, Regional",
                M.COL_RATING: 4.0,
                M.COL_COST_FOR_TWO: 100.0,
                M.COL_RAW_FEATURES: "",
                M.COL_VOTES: 1,
                M.COL_SOURCE_INDEX: 0,
            }
        ]
    )
    cat = build_cuisine_catalog(df)
    assert cat == ["Italian", "Regional"]


def test_resolve_typo_to_catalog():
    cat = ["Italian", "Chinese", "North Indian"]
    assert resolve_primary_cuisine("Italin", cat) == "Italian"
    assert resolve_primary_cuisine("ITALIAN", cat) == "Italian"
    assert resolve_primary_cuisine("Italian", cat) == "Italian"


def test_resolve_containment():
    cat = ["North Indian", "South Indian", "Italian"]
    assert resolve_primary_cuisine("North", cat) in ("North Indian",)


def test_resolve_unknown_unchanged():
    cat = ["Italian"]
    assert resolve_primary_cuisine("TotallyUnknownXyz", cat) == "TotallyUnknownXyz"
