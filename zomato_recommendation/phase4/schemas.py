"""HTTP request/response models (architecture §6.1)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from zomato_recommendation.phase3.schemas import RecommendationMeta, RestaurantRecommendation


class RecommendationRequest(BaseModel):
    """``POST /api/v1/recommendations`` — only ``location`` is required; other fields refine the search."""

    location: str = Field(..., min_length=1)
    budget_max_inr: float | None = Field(
        default=None,
        description="Maximum approximate cost for two (INR); omit to ignore budget.",
    )
    cuisine: str = ""
    min_rating: float | None = Field(default=None, description="Omit to include any rating.")
    extras: str | list[str] = ""
    secondary_cuisines: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @field_validator("location")
    @classmethod
    def strip_location(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty")
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
            raise ValueError("budget_max_inr must be positive and at most 10_000_000")
        return v

    @field_validator("min_rating")
    @classmethod
    def rating_if_set(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0.0 or v > 5.0:
            raise ValueError("min_rating must be between 0 and 5")
        return v

    @field_validator("extras")
    @classmethod
    def extras_norm(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, list):
            return [x.strip() for x in v if x and str(x).strip()]
        return v.strip() if isinstance(v, str) else v


class RecommendationResponse(BaseModel):
    """§6.1 response shape plus optional fields."""

    summary: str | None = None
    recommendations: list[RestaurantRecommendation]
    meta: RecommendationMeta
    degraded: bool = False
    message: str | None = Field(
        default=None,
        description="Set when there are no matches or nothing to return.",
    )


class LocationsResponse(BaseModel):
    """``GET /api/v1/locations`` — distinct city and area strings from the loaded catalog."""

    locations: list[str]


class CuisinesResponse(BaseModel):
    """``GET /api/v1/cuisines`` — distinct cuisine tokens from the loaded dataset only."""

    cuisines: list[str]
