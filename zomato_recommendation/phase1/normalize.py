from __future__ import annotations

import hashlib
import re
from typing import Any

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (ValueError, TypeError):
        return False


def parse_zomato_rate(value: Any) -> float | None:
    """Parse HF `rate` field (e.g. '4.1/5', 'NEW', '-') to a float or None."""
    if _is_null(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    upper = s.upper()
    if upper in ("NEW", "-", "NAN", "NONE"):
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(1))
    return None


def parse_approx_cost_for_two(value: Any) -> float | None:
    """
    Parse `approx_cost(for two people)` into a single numeric estimate (e.g. INR for two).

    Handles forms like '800', '1,200', '800,1200', ranges by averaging detected numbers.
    """
    if _is_null(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    # Token runs of digits with optional thousand commas / decimals
    raw_tokens = re.findall(r"\d[\d,]*(?:\.\d+)?", s)
    vals: list[float] = []
    for tok in raw_tokens:
        try:
            vals.append(float(tok.replace(",", "")))
        except ValueError:
            continue
    if not vals:
        return None
    return sum(vals) / len(vals)


def parse_votes(value: Any) -> int:
    if _is_null(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def normalize_cuisines(value: Any) -> str:
    if _is_null(value):
        return ""
    s = str(value).strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s


def _shorten_text(value: Any, max_len: int = 1200) -> str:
    if _is_null(value):
        return ""
    text = str(value).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_raw_features(row: pd.Series) -> str:
    """Optional blob for LLM context: area, types, menu hints, truncated reviews."""
    chunks: list[str] = []
    loc = row.get(M.HF_LOCATION)
    if not _is_null(loc):
        chunks.append(f"Area: {loc}")
    rt = row.get(M.HF_REST_TYPE)
    if not _is_null(rt):
        chunks.append(f"Establishment: {rt}")
    lit = row.get(M.HF_LISTED_IN_TYPE)
    if not _is_null(lit):
        chunks.append(f"Listed as: {lit}")
    dish = row.get(M.HF_DISH_LIKED)
    if not _is_null(dish):
        chunks.append(f"Dish liked: {_shorten_text(dish, 400)}")
    menu = row.get(M.HF_MENU_ITEM)
    if not _is_null(menu):
        chunks.append(f"Menu sample: {_shorten_text(menu, 400)}")
    rev = row.get(M.HF_REVIEWS_LIST)
    if not _is_null(rev):
        chunks.append(f"Reviews (excerpt): {_shorten_text(rev, 800)}")
    addr = row.get(M.HF_ADDRESS)
    if not _is_null(addr):
        chunks.append(f"Address: {_shorten_text(addr, 300)}")
    return "\n".join(chunks)


def make_stable_row_id(source_index: int, name: str, city: str, location: str) -> str:
    payload = f"{source_index}\0{name}\0{city}\0{location}".encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()[:16]


def normalize_restaurants_dataframe(
    raw: pd.DataFrame,
    *,
    source_index_start: int = 0,
) -> pd.DataFrame:
    """
    Map Hugging Face columns to the canonical schema (architecture §4.2).

    Parameters
    ----------
    raw :
        DataFrame whose columns include those listed in ``field_mapping.HF_COLUMNS_USED``.
    source_index_start :
        Offset added to the row position so IDs stay unique when loading slices.
    """
    df = raw.copy()
    for col in M.HF_COLUMNS_USED:
        if col not in df.columns:
            df[col] = None

    n = len(df)
    source_indices = list(range(source_index_start, source_index_start + n))

    names = df[M.HF_NAME].map(lambda x: "" if _is_null(x) else str(x).strip())
    cities = df[M.HF_LISTED_IN_CITY].map(lambda x: "" if _is_null(x) else str(x).strip())
    locations = df[M.HF_LOCATION].map(lambda x: "" if _is_null(x) else str(x).strip())

    ids = [
        make_stable_row_id(source_indices[i], names.iloc[i], cities.iloc[i], locations.iloc[i])
        for i in range(n)
    ]

    ratings = df[M.HF_RATE].map(parse_zomato_rate)
    costs = df[M.HF_APPROX_COST].map(parse_approx_cost_for_two)
    cuisines = df[M.HF_CUISINES].map(normalize_cuisines)
    votes = df[M.HF_VOTES].map(parse_votes)

    raw_features = df.apply(build_raw_features, axis=1)

    out = pd.DataFrame(
        {
            M.COL_ID: ids,
            M.COL_NAME: names,
            M.COL_CITY: cities,
            M.COL_LOCATION: locations,
            M.COL_CUISINES: cuisines,
            M.COL_RATING: ratings,
            M.COL_COST_FOR_TWO: costs,
            M.COL_RAW_FEATURES: raw_features,
            M.COL_VOTES: votes,
            M.COL_SOURCE_INDEX: source_indices,
        }
    )
    return out
