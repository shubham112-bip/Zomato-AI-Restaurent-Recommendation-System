"""
Candidate selection: filter, relax, sort, top-K (architecture §5.2, Phase 2).

Deterministic only — no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M
from zomato_recommendation.phase2.location_aliases import row_matches_location, search_terms_for_location
from zomato_recommendation.phase2.preferences import UserPreferences


@dataclass
class CandidateSelectionResult:
    """Outcome of ``select_candidates`` (for API metadata)."""

    candidates: pd.DataFrame
    constraints_relaxed: bool
    relaxation_steps: list[str] = field(default_factory=list)


def _extras_terms(prefs: UserPreferences) -> list[str]:
    ex = prefs.extras
    if isinstance(ex, list):
        return [t.casefold() for t in ex if t]
    if isinstance(ex, str) and ex.strip():
        return [ex.strip().casefold()]
    return []


def _extras_boost_score(raw: str, terms: list[str]) -> int:
    if not terms:
        return 0
    blob = raw.casefold()
    return 1 if any(t in blob for t in terms) else 0


def _matches_cuisine(cuisines: str, primary: str, secondaries: list[str], require_secondaries: bool) -> bool:
    if not primary.strip():
        return True
    blob = cuisines.casefold()
    if primary.casefold() not in blob:
        return False
    if require_secondaries and secondaries:
        for s in secondaries:
            if s.casefold() not in blob:
                return False
    return True


def _pass_budget_inr(cost: Any, budget_max_inr: float | None, relax_step: int) -> bool:
    """
    ``relax_step`` 0: cost <= ``budget_max_inr``; 1/2: widen multipliers; 3+: no cap.
    Unknown cost is included (same as legacy tier behavior).
    If ``budget_max_inr`` is None, no budget filter.
    """
    if budget_max_inr is None:
        return True
    if relax_step >= 3:
        return True
    ceiling = budget_max_inr
    if relax_step == 1:
        ceiling = budget_max_inr * 1.25
    elif relax_step == 2:
        ceiling = budget_max_inr * 1.50
    if cost is None or (isinstance(cost, float) and pd.isna(cost)):
        return True
    try:
        c = float(cost)
    except (TypeError, ValueError):
        return True
    return c <= ceiling


def _apply_pipeline(
    df: pd.DataFrame,
    prefs: UserPreferences,
    *,
    location_terms: list[str],
    require_secondaries: bool,
    min_rating: float | None,
    budget_relax_step: int,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    m = pd.Series(True, index=df.index)
    m &= df.apply(
        lambda r: row_matches_location(str(r[M.COL_CITY]), str(r[M.COL_LOCATION]), location_terms),
        axis=1,
    )
    if min_rating is not None:
        m &= df[M.COL_RATING].notna() & (df[M.COL_RATING] >= min_rating)
    m &= df.apply(
        lambda r: _matches_cuisine(str(r[M.COL_CUISINES]), prefs.cuisine, prefs.secondary_cuisines, require_secondaries),
        axis=1,
    )
    m &= df.apply(
        lambda r: _pass_budget_inr(r[M.COL_COST_FOR_TWO], prefs.budget_max_inr, budget_relax_step),
        axis=1,
    )
    return df.loc[m].copy()


def _sort_candidates(df: pd.DataFrame, prefs: UserPreferences) -> pd.DataFrame:
    terms = _extras_terms(prefs)
    if terms:
        scores = df[M.COL_RAW_FEATURES].map(lambda x: _extras_boost_score(str(x), terms))
        work = df.assign(_extras_score=scores)
        work = work.sort_values(
            by=["_extras_score", M.COL_RATING, M.COL_VOTES],
            ascending=[False, False, False],
            na_position="last",
            kind="mergesort",
        )
        return work.drop(columns=["_extras_score"])
    return df.sort_values(
        by=[M.COL_RATING, M.COL_VOTES],
        ascending=[False, False],
        na_position="last",
        kind="mergesort",
    )


def _dedupe_by_restaurant_identity(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (name, city, neighborhood). The HF dataset can list the same venue twice with
    different ``source_index``-derived ids; keep the first row after sort (best rating/votes).
    """
    if df.empty:
        return df
    key = (
        df[M.COL_NAME].astype(str).str.strip().str.casefold()
        + "\x00"
        + df[M.COL_CITY].astype(str).str.strip().str.casefold()
        + "\x00"
        + df[M.COL_LOCATION].astype(str).str.strip().str.casefold()
    )
    return df.loc[~key.duplicated(keep="first")].copy()


def select_candidates(
    df: pd.DataFrame,
    prefs: UserPreferences,
    *,
    top_k: int = 30,
    k_min: int = 5,
    min_rating_floor: float = 2.0,
    min_rating_step: float = 0.5,
) -> CandidateSelectionResult:
    """
    Filter normalized restaurants, relax until at least ``k_min`` rows or no more relaxation,
    then sort and return at most ``top_k`` rows.

    Relaxation order matches architecture §5.2: location widen → budget steps → drop secondary
    cuisine → lower ``min_rating`` in steps.
    """
    required_cols = set(M.CANONICAL_COLUMNS)
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing canonical columns: {sorted(missing)}")

    if df.empty:
        return CandidateSelectionResult(
            candidates=pd.DataFrame(columns=list(M.CANONICAL_COLUMNS)),
            constraints_relaxed=False,
            relaxation_steps=[],
        )

    steps: list[str] = []
    relaxed = False

    widen_location = False
    budget_relax = 0
    require_secondaries = bool(prefs.secondary_cuisines) and bool(prefs.cuisine.strip())
    min_rating: float | None = prefs.min_rating

    def one_pass() -> pd.DataFrame:
        terms = search_terms_for_location(prefs.location, widen=widen_location)
        if not terms:
            return pd.DataFrame(columns=df.columns)
        out = _apply_pipeline(
            df,
            prefs,
            location_terms=terms,
            require_secondaries=require_secondaries,
            min_rating=min_rating,
            budget_relax_step=budget_relax,
        )
        out = _sort_candidates(out, prefs)
        return _dedupe_by_restaurant_identity(out)

    result = one_pass()

    def relax() -> bool:
        nonlocal widen_location, budget_relax, require_secondaries, min_rating, relaxed
        if not widen_location:
            widen_location = True
            steps.append("widen_location_aliases")
            relaxed = True
            return True
        if budget_relax < 3:
            budget_relax += 1
            steps.append(f"relax_budget_step_{budget_relax}")
            relaxed = True
            return True
        if prefs.secondary_cuisines and require_secondaries:
            require_secondaries = False
            steps.append("drop_secondary_cuisine")
            relaxed = True
            return True
        if min_rating is not None and min_rating > min_rating_floor:
            min_rating = max(min_rating_floor, min_rating - min_rating_step)
            steps.append(f"lower_min_rating_to_{min_rating}")
            relaxed = True
            return True
        return False

    while len(result) < k_min and relax():
        result = one_pass()

    result = result.head(top_k)
    return CandidateSelectionResult(
        candidates=result.reset_index(drop=True),
        constraints_relaxed=relaxed,
        relaxation_steps=steps,
    )
