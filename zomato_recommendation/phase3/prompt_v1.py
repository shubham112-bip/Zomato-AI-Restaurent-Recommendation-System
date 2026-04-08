"""Versioned prompts (architecture §5.3). ``PROMPT_VERSION`` lives in ``schemas.py``."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase2.preferences import UserPreferences


def _prefs_bullets(prefs: UserPreferences) -> str:
    lines = [f"- Location: {prefs.location}"]
    if prefs.budget_max_inr is not None:
        lines.append(f"- Budget (max approximate cost for two, INR): {prefs.budget_max_inr:.0f}")
    else:
        lines.append("- Budget: not specified (any)")
    if prefs.cuisine.strip():
        lines.append(f"- Cuisine (primary): {prefs.cuisine}")
    else:
        lines.append("- Cuisine: any")
    if prefs.min_rating is not None:
        lines.append(f"- Minimum rating: {prefs.min_rating}")
    else:
        lines.append("- Minimum rating: not specified (include all ratings)")
    if prefs.secondary_cuisines:
        lines.append(f"- Secondary cuisines: {', '.join(prefs.secondary_cuisines)}")
    ex = prefs.extras
    if isinstance(ex, list) and ex:
        lines.append(f"- Extras: {', '.join(ex)}")
    elif isinstance(ex, str) and ex.strip():
        lines.append(f"- Extras: {ex.strip()}")
    return "\n".join(lines)


def _candidates_table_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        cost = r.get(M.COL_COST_FOR_TWO)
        cost_out: float | None
        try:
            if cost is None or (isinstance(cost, float) and pd.isna(cost)):
                cost_out = None
            else:
                cost_out = float(cost)
        except (TypeError, ValueError):
            cost_out = None
        raw = str(r.get(M.COL_RAW_FEATURES, ""))[:600]
        rows.append(
            {
                "id": str(r[M.COL_ID]),
                "name": str(r[M.COL_NAME]),
                "cuisines": str(r[M.COL_CUISINES]),
                "rating": float(r[M.COL_RATING]) if pd.notna(r.get(M.COL_RATING)) else None,
                "cost_for_two_inr": cost_out,
                "area": str(r.get(M.COL_LOCATION, "")),
                "city": str(r.get(M.COL_CITY, "")),
                "notes": raw,
            }
        )
    return rows


def build_system_message(top_n: int) -> str:
    return (
        "You are a restaurant recommendation assistant. "
        "You must ONLY recommend restaurants whose `id` appears in the provided candidate list. "
        "Do not invent restaurants or IDs. "
        f"Respond with a single JSON object (no markdown fences) with this shape exactly:\n"
        '{"summary": string or null, "recommendations": ['
        '{"id": string, "rank": integer, "explanation": string (2-4 sentences), '
        '"confidence": number or null}]} '
        f"Include at most {top_n} items in `recommendations`, ordered by rank ascending (1 is best). "
        "If no candidate fits the user, return an empty `recommendations` array and a short summary explaining why."
    )


def build_user_message(candidates: pd.DataFrame, prefs: UserPreferences, top_n: int) -> str:
    payload = {
        "user_preferences": _prefs_bullets(prefs),
        "candidates": _candidates_table_rows(candidates),
        "task": (
            f"Rank and explain the top up to {top_n} restaurants from `candidates` only. "
            "Each explanation must justify the pick using preferences and the candidate fields."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_messages(candidates: pd.DataFrame, prefs: UserPreferences, top_n: int) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_system_message(top_n)},
        {"role": "user", "content": build_user_message(candidates, prefs, top_n)},
    ]


def build_fix_json_user_message(bad_content: str) -> str:
    return (
        "Your previous reply was not valid JSON. "
        "Return ONLY one JSON object matching the schema from the system message, with no markdown. "
        "Previous content (for debugging, fix it):\n\n"
        f"{bad_content[:8000]}"
    )
