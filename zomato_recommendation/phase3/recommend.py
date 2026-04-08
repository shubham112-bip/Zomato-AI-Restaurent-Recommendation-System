"""Orchestrate Groq call, parse, merge, and fallback (architecture §5.3–5.4)."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pandas as pd

from zomato_recommendation.phase2.preferences import UserPreferences
from zomato_recommendation.phase3.fallback import candidates_to_fallback_payload
from zomato_recommendation.phase3.groq_client import call_groq_chat
from zomato_recommendation.phase3.merge import merge_llm_payload
from zomato_recommendation.phase3.parse import parse_llm_json
from zomato_recommendation.phase3.prompt_v1 import build_fix_json_user_message, build_messages
from zomato_recommendation.phase3.schemas import (
    PROMPT_VERSION,
    GroqRecommendationResult,
    RecommendationMeta,
    RestaurantRecommendation,
)
from zomato_recommendation.phase3.settings import GroqSettings, get_groq_settings

logger = logging.getLogger(__name__)


def _run_parse_or_none(content: str):
    try:
        return parse_llm_json(content)
    except ValueError as e:
        logger.warning("LLM JSON parse failed: %s", e)
        return None


def recommend_with_groq(
    candidates: pd.DataFrame,
    prefs: UserPreferences,
    *,
    top_n: int = 5,
    constraints_relaxed: bool = False,
    settings: GroqSettings | None = None,
    completion_fn: Callable[..., str] | None = None,
) -> GroqRecommendationResult:
    """
    Rank and explain up to ``top_n`` rows using Groq, then merge to display DTOs.

    Parameters
    ----------
    candidates :
        Normalized Phase 2 candidate dataframe (may be empty).
    completion_fn :
        Optional override for tests: ``fn(messages=..., model=...) -> content string``.
        When omitted, uses ``call_groq_chat`` (requires ``GROQ_API_KEY``).
    """
    settings = settings or get_groq_settings()
    meta_base = RecommendationMeta(
        candidates_considered=len(candidates),
        constraints_relaxed=constraints_relaxed,
        model=settings.groq_model,
        prompt_version=PROMPT_VERSION,
    )

    if candidates.empty:
        return GroqRecommendationResult(
            summary=None,
            recommendations=[],
            meta=meta_base,
            degraded=False,
        )

    messages = build_messages(candidates, prefs, top_n)

    def complete(msgs: list[dict[str, str]]) -> str:
        if completion_fn is not None:
            return completion_fn(messages=msgs, model=settings.groq_model)
        return call_groq_chat(msgs, settings=settings)

    degraded = False
    content = complete(messages)
    payload = _run_parse_or_none(content)

    if payload is None:
        fix_msgs = list(messages)
        fix_msgs.append({"role": "assistant", "content": content})
        fix_msgs.append({"role": "user", "content": build_fix_json_user_message(content)})
        content2 = complete(fix_msgs)
        payload = _run_parse_or_none(content2)

    if payload is None:
        logger.warning("Using deterministic fallback after LLM JSON failures.")
        payload = candidates_to_fallback_payload(candidates, top_n)
        degraded = True

    merged, dropped = merge_llm_payload(payload, candidates, top_n=top_n)
    if dropped:
        logger.debug("Dropped unknown LLM ids: %s", dropped)

    if not merged and not degraded and len(candidates) > 0 and payload.recommendations:
        logger.warning("All LLM recommendation ids were unknown; using deterministic fallback.")
        payload = candidates_to_fallback_payload(candidates, top_n)
        degraded = True
        merged, _ = merge_llm_payload(payload, candidates, top_n=top_n)

    # Re-assign contiguous ranks 1..n for display consistency
    recs: list[RestaurantRecommendation] = [
        r.model_copy(update={"rank": i + 1}) for i, r in enumerate(merged[:top_n])
    ]

    return GroqRecommendationResult(
        summary=payload.summary,
        recommendations=recs,
        meta=meta_base,
        degraded=degraded,
    )
