"""Cuisine tokens from the loaded dataset and fuzzy resolution against that list only."""

from __future__ import annotations

import difflib

import pandas as pd

from zomato_recommendation.phase1 import field_mapping as M


def distinct_cuisine_tokens(df: pd.DataFrame) -> list[str]:
    """Split ``cuisines`` on commas and return distinct non-empty tokens (case-insensitive dedupe, sorted)."""
    if df is None or len(df) == 0 or M.COL_CUISINES not in df.columns:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for cell in df[M.COL_CUISINES].dropna().astype(str):
        for part in cell.split(","):
            t = part.strip()
            if not t:
                continue
            k = t.casefold()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
    out.sort(key=lambda s: s.casefold())
    return out


def build_cuisine_catalog(df: pd.DataFrame) -> list[str]:
    """All cuisine labels used for suggestions, fuzzy matching, and validation — **dataset only** (no static list)."""
    return distinct_cuisine_tokens(df)


def resolve_primary_cuisine(user_raw: str, catalog: list[str]) -> str:
    """
    Map free-text or typo input to a canonical catalog label when possible.

    Order: exact case-insensitive match → containment in a catalog token → difflib close match → unchanged input.
    Empty input stays empty (any cuisine).
    """
    u = user_raw.strip()
    if not u:
        return ""
    cat = _dedupe_preserve_order(catalog)
    if not cat:
        return u
    u_cf = u.casefold()
    cf_to_display = {c.casefold(): c for c in cat}

    if u_cf in cf_to_display:
        return cf_to_display[u_cf]

    contain = [c for c in cat if u_cf in c.casefold() or c.casefold() in u_cf]
    if contain:
        if len(contain) == 1:
            return contain[0]
        keys = [c.casefold() for c in contain]
        best = difflib.get_close_matches(u_cf, keys, n=1, cutoff=0.35)
        if best:
            return cf_to_display[best[0]]
        return min(contain, key=len)

    keys = list(cf_to_display.keys())
    best = difflib.get_close_matches(u_cf, keys, n=1, cutoff=0.55)
    if best:
        return cf_to_display[best[0]]
    return u


def is_known_cuisine_label(label: str, catalog: list[str]) -> bool:
    """True if ``label`` matches a catalog entry case-insensitively."""
    if not label.strip() or not catalog:
        return True
    ci = {c.casefold() for c in catalog}
    return label.casefold() in ci


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        s = x.strip()
        if not s:
            continue
        k = s.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out
