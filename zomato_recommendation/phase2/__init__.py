"""Phase 2 — preferences, filtering, candidate selection (architecture §5.1–5.2)."""

from zomato_recommendation.phase2.preferences import UserPreferences
from zomato_recommendation.phase2.selection import CandidateSelectionResult, select_candidates

__all__ = [
    "CandidateSelectionResult",
    "UserPreferences",
    "select_candidates",
]
