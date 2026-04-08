"""Deterministic fallback when LLM JSON fails (architecture §5.3)."""

from __future__ import annotations

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase3.merge import _format_cost
from zomato_recommendation.phase3.schemas import LlmPayload, LlmRecommendationItem


def candidates_to_fallback_payload(candidates: pd.DataFrame, top_n: int) -> LlmPayload:
    """Top rows by rating then votes (same sort idea as Phase 2)."""
    if candidates.empty:
        return LlmPayload(summary="No candidates to rank.", recommendations=[])
    work = candidates.sort_values(
        by=[M.COL_RATING, M.COL_VOTES],
        ascending=[False, False],
        na_position="last",
        kind="mergesort",
    ).head(top_n)
    items: list[LlmRecommendationItem] = []
    for i, (_, row) in enumerate(work.iterrows(), start=1):
        items.append(
            LlmRecommendationItem(
                id=str(row[M.COL_ID]),
                rank=i,
                explanation=(
                    "Selected by rating and popularity from the filtered list "
                    "(automated fallback while the AI summary was unavailable)."
                ),
            )
        )
    return LlmPayload(
        summary="Recommendations shown using deterministic ranking (LLM output was not usable).",
        recommendations=items,
    )


def format_cost_for_display(value: object) -> str:
    return _format_cost(value)
