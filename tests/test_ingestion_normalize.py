"""Unit tests for Phase 1 ingestion (no Hugging Face download required)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase1.load import (
    hf_raw_to_pandas,
    normalize_restaurants_dataframe,
    write_parquet_snapshot,
)
from zomato_recommendation.phase1.normalize import (
    parse_approx_cost_for_two,
    parse_zomato_rate,
)


@pytest.fixture
def tiny_hf_fixture() -> pd.DataFrame:
    """Two synthetic rows matching HF column names."""
    return pd.DataFrame(
        [
            {
                M.HF_NAME: "Test Diner",
                M.HF_LOCATION: "Koramangala",
                M.HF_LISTED_IN_CITY: "Bangalore",
                M.HF_LISTED_IN_TYPE: "Delivery",
                M.HF_RATE: "4.2/5",
                M.HF_VOTES: 120,
                M.HF_CUISINES: "Chinese, Thai",
                M.HF_APPROX_COST: "800",
                M.HF_REVIEWS_LIST: "[('Rated 4.0', 'Good food')]",
                M.HF_MENU_ITEM: "Soup",
                M.HF_DISH_LIKED: "Noodles",
                M.HF_REST_TYPE: "Casual Dining",
                M.HF_ADDRESS: "1 Main Rd",
            },
            {
                M.HF_NAME: "New Place",
                M.HF_LOCATION: "CP",
                M.HF_LISTED_IN_CITY: "New Delhi",
                M.HF_LISTED_IN_TYPE: "Dine-out",
                M.HF_RATE: "NEW",
                M.HF_VOTES: 0,
                M.HF_CUISINES: "  Italian ",
                M.HF_APPROX_COST: "1,200",
                M.HF_REVIEWS_LIST: "",
                M.HF_MENU_ITEM: "",
                M.HF_DISH_LIKED: "",
                M.HF_REST_TYPE: "",
                M.HF_ADDRESS: "",
            },
        ]
    )


def test_parse_zomato_rate():
    assert parse_zomato_rate("4.1/5") == pytest.approx(4.1)
    assert parse_zomato_rate("NEW") is None
    assert parse_zomato_rate(None) is None


def test_parse_approx_cost_for_two():
    assert parse_approx_cost_for_two("800") == pytest.approx(800.0)
    assert parse_approx_cost_for_two("1,200") == pytest.approx(1200.0)
    assert parse_approx_cost_for_two("800,1200") == pytest.approx(1000.0)
    assert parse_approx_cost_for_two("") is None


def test_normalize_restaurants_dataframe_columns_and_types(tiny_hf_fixture: pd.DataFrame):
    out = normalize_restaurants_dataframe(tiny_hf_fixture, source_index_start=0)
    assert list(out.columns) == list(M.CANONICAL_COLUMNS)
    assert len(out) == 2
    assert out[M.COL_NAME].iloc[0] == "Test Diner"
    assert out[M.COL_CITY].iloc[0] == "Bangalore"
    assert out[M.COL_RATING].iloc[0] == pytest.approx(4.2)
    assert pd.isna(out[M.COL_RATING].iloc[1])
    assert out[M.COL_COST_FOR_TWO].iloc[0] == pytest.approx(800.0)
    assert out[M.COL_COST_FOR_TWO].iloc[1] == pytest.approx(1200.0)
    assert out[M.COL_CUISINES].iloc[1] == "Italian"
    assert out[M.COL_VOTES].iloc[0] == 120
    assert out[M.COL_VOTES].iloc[1] == 0
    assert out[M.COL_SOURCE_INDEX].tolist() == [0, 1]
    assert len(out[M.COL_ID].iloc[0]) == 16
    assert M.COL_RAW_FEATURES in out.columns
    assert "Koramangala" in out[M.COL_RAW_FEATURES].iloc[0]


def test_hf_raw_to_pandas_adds_missing_columns():
    minimal = pd.DataFrame([{M.HF_NAME: "Only"}])
    full = hf_raw_to_pandas(minimal)
    assert M.HF_CUISINES in full.columns
    assert pd.isna(full[M.HF_CUISINES].iloc[0])


def test_write_parquet_snapshot_roundtrip(tiny_hf_fixture: pd.DataFrame):
    out = normalize_restaurants_dataframe(tiny_hf_fixture)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "snap.parquet"
        write_parquet_snapshot(out, path)
        back = pd.read_parquet(path)
    pd.testing.assert_frame_equal(out.reset_index(drop=True), back.reset_index(drop=True))


def test_source_index_offset():
    df = pd.DataFrame(
        [
            {
                M.HF_NAME: "A",
                M.HF_LOCATION: "x",
                M.HF_LISTED_IN_CITY: "y",
                M.HF_LISTED_IN_TYPE: "",
                M.HF_RATE: "3/5",
                M.HF_VOTES: 1,
                M.HF_CUISINES: "X",
                M.HF_APPROX_COST: "100",
                M.HF_REVIEWS_LIST: "",
                M.HF_MENU_ITEM: "",
                M.HF_DISH_LIKED: "",
                M.HF_REST_TYPE: "",
                M.HF_ADDRESS: "",
            }
        ]
    )
    out = normalize_restaurants_dataframe(df, source_index_start=100)
    assert out[M.COL_SOURCE_INDEX].iloc[0] == 100
