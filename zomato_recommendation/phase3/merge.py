"""Join LLM ids to candidate rows (architecture §5.4)."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase3.schemas import LlmPayload, RestaurantRecommendation

logger = logging.getLogger(__name__)


def _format_cost(value: Any) -> str:
    if value is None:
        return "Unknown"
    try:
        if isinstance(value, float) and pd.isna(value):
            return "Unknown"
        v = float(value)
    except (TypeError, ValueError):
        return "Unknown"
    if v != v:  # NaN
        return "Unknown"
    return f"₹{int(round(v))}"


def merge_llm_payload(
    payload: LlmPayload,
    candidates: pd.DataFrame,
    *,
    top_n: int,
) -> tuple[list[RestaurantRecommendation], list[str]]:
    """
    Build display rows; drop unknown ids (log).

    Returns ``(recommendations, dropped_ids)``.
    """
    by_id = candidates.set_index(M.COL_ID, drop=False)
    out: list[RestaurantRecommendation] = []
    dropped: list[str] = []

    sorted_items = sorted(payload.recommendations, key=lambda x: (x.rank, x.id))
    seen_ids: set[str] = set()

    for item in sorted_items:
        if len(out) >= top_n:
            break
        rid = item.id
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        if rid not in by_id.index:
            dropped.append(rid)
            logger.debug("LLM returned unknown id: %s", rid)
            continue
        row = by_id.loc[rid]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        rating = row[M.COL_RATING]
        rating_f: float | None
        if pd.isna(rating):
            rating_f = None
        else:
            try:
                rating_f = float(rating)
            except (TypeError, ValueError):
                rating_f = None
        out.append(
            RestaurantRecommendation(
                name=str(row[M.COL_NAME]),
                cuisine=str(row[M.COL_CUISINES]),
                rating=rating_f,
                estimated_cost=_format_cost(row[M.COL_COST_FOR_TWO]),
                explanation=item.explanation,
                rank=item.rank,
            )
        )

    return out, dropped
