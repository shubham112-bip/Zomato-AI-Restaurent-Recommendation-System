"""Pydantic models for LLM JSON and API-style responses (architecture §5.3–5.4, §6.1)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


PROMPT_VERSION = "v1"


class LlmRecommendationItem(BaseModel):
    """Single row in the LLM JSON output."""

    id: str
    rank: int
    explanation: str
    confidence: float | None = None


class LlmPayload(BaseModel):
    """Expected JSON object from the model."""

    summary: str | None = None
    recommendations: list[LlmRecommendationItem] = Field(default_factory=list)


class RestaurantRecommendation(BaseModel):
    """One merged display row (architecture §5.4)."""

    name: str
    cuisine: str
    rating: float | None
    estimated_cost: str
    explanation: str
    rank: int


class RecommendationMeta(BaseModel):
    """Metadata aligned with §6.1 ``meta``."""

    candidates_considered: int
    constraints_relaxed: bool = False
    model: str
    prompt_version: str = PROMPT_VERSION
    cuisine_resolved: str | None = Field(
        default=None,
        description="Canonical cuisine label used for filtering when it differs from the request (typo/casing/nearest match).",
    )


class GroqRecommendationResult(BaseModel):
    """Full Phase 3 outcome for callers / future API."""

    summary: str | None
    recommendations: list[RestaurantRecommendation]
    meta: RecommendationMeta
    degraded: bool = Field(
        default=False,
        description="True if deterministic fallback was used (architecture §5.3 failure handling).",
    )


class GroqCompletionFn(Protocol):
    """Callable shape for tests (mock Groq)."""

    def __call__(self, *, messages: list[dict[str, str]], model: str) -> str: ...
