"""User preference model (architecture §5.1)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class UserPreferences(BaseModel):
    """Validated preferences for candidate filtering (API boundary shape)."""

    location: str = Field(
        ...,
        min_length=1,
        description="City or area; matched against city and neighborhood columns.",
    )
    budget_max_inr: float | None = Field(
        default=None,
        description="Max cost for two (INR); omit to skip budget filtering.",
    )
    cuisine: str = Field(
        default="",
        description="Primary cuisine substring; empty means any cuisine.",
    )
    min_rating: float | None = Field(
        default=None,
        description="Minimum rating; omit to include all ratings (including missing).",
    )
    secondary_cuisines: list[str] = Field(
        default_factory=list,
        description="Optional; all must appear when non-empty (until relaxed).",
    )
    extras: str | list[str] = Field(
        default="",
        description="Free-text tags for LLM / optional keyword sort (not strict filter).",
    )

    model_config = {"extra": "forbid"}

    @field_validator("location")
    @classmethod
    def strip_nonempty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s

    @field_validator("cuisine", mode="before")
    @classmethod
    def cuisine_strip(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("budget_max_inr")
    @classmethod
    def budget_if_set(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v <= 0.0 or v > 10_000_000.0:
            raise ValueError("budget_max_inr must be between 0 exclusive and 10_000_000")
        return v

    @field_validator("min_rating")
    @classmethod
    def rating_if_set(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0.0 or v > 5.0:
            raise ValueError("min_rating must be between 0 and 5")
        return v

    @field_validator("secondary_cuisines")
    @classmethod
    def strip_secondaries(cls, v: list[str]) -> list[str]:
        out = [x.strip() for x in v if x and str(x).strip()]
        return out

    @field_validator("extras")
    @classmethod
    def normalize_extras(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, list):
            return [x.strip() for x in v if x and str(x).strip()]
        return v.strip()
