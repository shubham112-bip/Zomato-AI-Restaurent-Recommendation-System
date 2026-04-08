"""
Inspect raw Hugging Face schema and a normalized sample (requires network on first load).

Usage::

    python -m zomato_recommendation.phase1.inspect_dataset
"""

from __future__ import annotations

import argparse
import json

from datasets import load_dataset

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase1.load import hf_raw_to_pandas, normalize_restaurants_dataframe


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect HF Zomato dataset schema and sample rows.")
    parser.add_argument("--rows", type=int, default=3, help="Number of sample rows to print after normalize.")
    parser.add_argument("--max-chars", type=int, default=400, help="Truncate long fields in JSON dump.")
    args = parser.parse_args()

    split_arg = f"train[:{args.rows}]"
    print(f"Loading {M.DATASET_NAME!r} split={split_arg!r} ...\n")
    ds = load_dataset(M.DATASET_NAME, split=split_arg)
    print("Features (raw):")
    print(ds.features)
    print()

    raw = hf_raw_to_pandas(ds)
    print("Raw columns:", list(raw.columns))
    print()

    norm = normalize_restaurants_dataframe(raw, source_index_start=0)
    print("Canonical columns:", list(norm.columns))
    print()

    def trunc(val: object) -> object:
        s = json.dumps(val, default=str)
        if len(s) > args.max_chars:
            return s[: args.max_chars] + "..."
        return val

    records = norm.to_dict(orient="records")
    for i, rec in enumerate(records):
        print(f"--- Normalized row {i} ---")
        safe = {k: trunc(v) for k, v in rec.items()}
        print(json.dumps(safe, indent=2, default=str))
        print()


if __name__ == "__main__":
    main()
