"""Orchestration: Phase 2 filter → Phase 3 Groq (architecture §7)."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pandas as pd
from fastapi import HTTPException

from zomato_recommendation.app_config import get_app_config
from zomato_recommendation.phase2.cuisine_catalog import (
    build_cuisine_catalog,
    is_known_cuisine_label,
    resolve_primary_cuisine,
)
from zomato_recommendation.phase2.preferences import UserPreferences
from zomato_recommendation.phase2.selection import select_candidates
from zomato_recommendation.phase3.recommend import recommend_with_groq
from zomato_recommendation.phase3.schemas import PROMPT_VERSION, GroqRecommendationResult, RecommendationMeta
from zomato_recommendation.phase3.settings import get_groq_settings
from zomato_recommendation.phase4.schemas import RecommendationRequest, RecommendationResponse

logger = logging.getLogger(__name__)

GroqFn = Callable[..., GroqRecommendationResult]


def request_to_preferences(body: RecommendationRequest, *, cuisine_primary: str) -> UserPreferences:
    return UserPreferences(
        location=body.location,
        budget_max_inr=body.budget_max_inr,
        cuisine=cuisine_primary,
        min_rating=body.min_rating,
        secondary_cuisines=body.secondary_cuisines,
        extras=body.extras,
    )


def _location_only_preferences(body: RecommendationRequest) -> bool:
    """True when only ``location`` constrains the search (list all restaurants in that area up to shortlist cap)."""
    return (
        not body.cuisine.strip()
        and body.budget_max_inr is None
        and body.min_rating is None
    )


def run_recommendations(
    body: RecommendationRequest,
    df: pd.DataFrame,
    *,
    groq_fn: GroqFn | None = None,
) -> RecommendationResponse:
    """
    Run filter + Groq. ``groq_fn`` defaults to ``recommend_with_groq`` (for tests, pass a stub).
    Shortlist size and default final ``top_n`` come from ``config.yaml``.
    When only ``location`` is provided, cuisine/budget/rating filters are skipped and ``top_n`` for the LLM
    is set to the shortlist size (up to ``filter.max_shortlist_candidates``) so every candidate row can appear.
    """
    cfg = get_app_config()
    catalog = build_cuisine_catalog(df)
    if body.cuisine.strip():
        resolved = resolve_primary_cuisine(body.cuisine, catalog)
        if catalog and not is_known_cuisine_label(resolved, catalog):
            raise HTTPException(
                status_code=422,
                detail="Cuisine must match a label from the loaded dataset. Use GET /api/v1/cuisines for allowed values.",
            )
        cuisine_resolved_meta: str | None = (
            resolved if resolved.casefold() != body.cuisine.strip().casefold() else None
        )
    else:
        resolved = ""
        cuisine_resolved_meta = None

    prefs = request_to_preferences(body, cuisine_primary=resolved)
    sel = select_candidates(
        df,
        prefs,
        top_k=cfg.max_shortlist_candidates,
        k_min=5,
    )

    location_only = _location_only_preferences(body)
    top_n_llm = (
        max(1, min(len(sel.candidates), cfg.max_shortlist_candidates))
        if location_only
        else cfg.top_n
    )

    if sel.candidates.empty:
        return RecommendationResponse(
            summary=None,
            recommendations=[],
            meta=RecommendationMeta(
                candidates_considered=0,
                constraints_relaxed=sel.constraints_relaxed,
                model=get_groq_settings().groq_model,
                prompt_version=PROMPT_VERSION,
                cuisine_resolved=cuisine_resolved_meta,
            ),
            degraded=False,
            message="No restaurants matched the filters. Try relaxing location, cuisine, or rating.",
        )

    fn = groq_fn or recommend_with_groq
    try:
        out = fn(
            sel.candidates,
            prefs,
            top_n=top_n_llm,
            constraints_relaxed=sel.constraints_relaxed,
        )
    except Exception as e:
        logger.exception("Groq recommendation failed: %s", e)
        raise

    msg: str | None = None
    if not out.recommendations:
        msg = "No recommendations produced. Try different preferences."

    meta = out.meta.model_copy(
        update={
            "candidates_considered": len(sel.candidates),
            "constraints_relaxed": sel.constraints_relaxed,
            "cuisine_resolved": cuisine_resolved_meta,
        }
    )

    return RecommendationResponse(
        summary=out.summary,
        recommendations=out.recommendations,
        meta=meta,
        degraded=out.degraded,
        message=msg,
    )
