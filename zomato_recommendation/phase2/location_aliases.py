"""Metro / city alias expansion (architecture §5.2 relaxation: widen location)."""

from __future__ import annotations

# Keys and values are matched case-insensitively against user input and dataset city/location.
METRO_ALIASES: dict[str, tuple[str, ...]] = {
    "bangalore": ("bangalore", "bengaluru"),
    "bengaluru": ("bangalore", "bengaluru"),
    "mumbai": ("mumbai", "bombay"),
    "bombay": ("mumbai", "bombay"),
    "new delhi": ("new delhi", "delhi", "ncr"),
    "delhi": ("new delhi", "delhi"),
    "gurgaon": ("gurgaon", "gurugram"),
    "gurugram": ("gurgaon", "gurugram"),
}


def search_terms_for_location(user_location: str, *, widen: bool) -> list[str]:
    """
    Build case-insensitive substring targets for city / neighborhood.

    When ``widen`` is False, use the user string only (plus trivial trim).
    When True, OR-in known aliases (e.g. Bangalore / Bengaluru).
    """
    base = user_location.strip()
    if not base:
        return []
    terms: list[str] = [base]
    key = base.casefold()
    if widen:
        for k, variants in METRO_ALIASES.items():
            if key == k or key in k or k in key or any(key == v.casefold() for v in variants):
                terms.extend(variants)
                terms.append(k)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        cf = t.casefold()
        if cf not in seen:
            seen.add(cf)
            out.append(t)
    return out


def row_matches_location(city: str, neighborhood: str, terms: list[str]) -> bool:
    city_cf = city.strip().casefold()
    loc_cf = neighborhood.strip().casefold()
    for t in terms:
        tc = t.casefold()
        if tc in city_cf or tc in loc_cf:
            return True
    return False
