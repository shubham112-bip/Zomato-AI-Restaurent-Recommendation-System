from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Dataset, load_dataset

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase1.normalize import normalize_restaurants_dataframe

__all__ = ["load_restaurants", "normalize_restaurants_dataframe", "hf_raw_to_pandas", "write_parquet_snapshot"]


def hf_raw_to_pandas(ds: Dataset | pd.DataFrame) -> pd.DataFrame:
    """Convert a Hugging Face split (or raw frame) to pandas with expected columns."""
    if isinstance(ds, pd.DataFrame):
        frame = ds.copy()
    else:
        frame = ds.to_pandas()
    for col in M.HF_COLUMNS_USED:
        if col not in frame.columns:
            frame[col] = None
    return frame[list(M.HF_COLUMNS_USED)]


def write_parquet_snapshot(df: pd.DataFrame, path: str | Path) -> None:
    """Write normalized dataframe to Parquet (optional Phase 1 cache)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def load_restaurants(
    *,
    split: str = M.DEFAULT_SPLIT,
    max_rows: int | None = None,
    cache_dir: str | None = None,
    export_parquet_path: str | Path | None = None,
    **load_dataset_kwargs: Any,
) -> pd.DataFrame:
    """
    Load the Zomato-style dataset from Hugging Face and return a normalized DataFrame.

    Parameters
    ----------
    split :
        Dataset split (default ``train``).
    max_rows :
        If set, only the first ``max_rows`` rows are loaded (faster for dev).
    cache_dir :
        Optional Hugging Face datasets cache directory.
    export_parquet_path :
        If set, write the normalized result to this Parquet path.
    **load_dataset_kwargs :
        Forwarded to ``datasets.load_dataset`` (e.g. ``revision=...`` for pinning).
    """
    split_arg = f"{split}[:{max_rows}]" if max_rows is not None else split
    ds = load_dataset(
        M.DATASET_NAME,
        split=split_arg,
        cache_dir=cache_dir,
        **load_dataset_kwargs,
    )
    raw = hf_raw_to_pandas(ds)
    # Splits like ``train[:100]`` start at row 0 of the underlying table.
    normalized = normalize_restaurants_dataframe(raw, source_index_start=0)
    if export_parquet_path is not None:
        write_parquet_snapshot(normalized, export_parquet_path)
    return normalized
