"""Phase 1 — data ingestion and normalization (architecture §4, §10 Phase 1)."""

from zomato_recommendation.phase1.load import (
    hf_raw_to_pandas,
    load_restaurants,
    normalize_restaurants_dataframe,
    write_parquet_snapshot,
)

__all__ = [
    "load_restaurants",
    "normalize_restaurants_dataframe",
    "hf_raw_to_pandas",
    "write_parquet_snapshot",
]
