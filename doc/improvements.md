# Improvements (tracked)

This document lists product and implementation improvements reflected in the **backend**, **frontend** (`zomato_recommendation/phase4/web/`), and **business logic**, with pointers into the codebase. See [architecture.md](./architecture.md) for the full system blueprint.

---

## 1. Location dropdown

| Layer | Details |
|--------|---------|
| **Backend** | `GET /api/v1/locations` returns distinct **city** and **neighborhood/area** strings from the loaded catalog (`city` and `location` columns), merged and deduplicated (case-insensitive). Implemented in `zomato_recommendation/phase4/app.py` (`_distinct_catalog_locations`). |
| **Frontend** | `phase4/web` (Next.js): location control populated after `/health` reports `dataset_ready`, via `fetch("/api/v1/locations")` (proxied through Next). |
| **Business logic** | Location matching uses substring search on city and area (`phase2/location_aliases.py`: `row_matches_location`, `search_terms_for_location`). |

---

## 2. Numeric budget

| Layer | Details |
|--------|---------|
| **Backend / API** | Request field `budget_max_inr` (optional). Omitted = no budget filter. |
| **Business logic** | `phase2/selection.py`: `_pass_budget_inr` — known `cost_for_two` must be `<=` effective cap per relaxation step (×1, ×1.25, ×1.5, then no cap). Tier labels (`low` / `medium` / `high`) are not used. |
| **LLM** | `phase3/prompt_v1.py`: `_prefs_bullets` includes a numeric INR line when set, or “not specified (any)”. |

---

## 3. Fixed shortlist size

| Layer | Details |
|--------|---------|
| **UI** | No user controls for shortlist size or final “how many picks” in the Next.js app. |
| **Config** | Root `config.yaml`: `filter.max_shortlist_candidates` (default **40**), `recommendations.top_n` (default **5**). Loaded by `zomato_recommendation/app_config.py`. |
| **Business logic** | `phase4/service.py`: `select_candidates(..., top_k=cfg.max_shortlist_candidates)`. Final `top_n` passed to Groq is `cfg.top_n` unless **location-only** mode (see §6). |

---

## 4. Optional preferences (only location required)

| Layer | Details |
|--------|---------|
| **Backend / API** | `phase4/schemas.py` — `RecommendationRequest`: **required** `location` only. Optional: `budget_max_inr`, `cuisine`, `min_rating`, `extras`, `secondary_cuisines`. |
| **Business logic** | `phase2/preferences.py` — empty cuisine = any cuisine; `budget_max_inr is None` = no budget filter; `min_rating is None` = no rating floor (includes missing ratings). `phase2/selection.py` applies filters accordingly. |
| **Frontend** | Only **Location** is required in the API; the Next.js form omits blank optional fields in the JSON payload. |

---

## 5. Location-only: list all venues in area (within caps)

| Layer | Details |
|--------|---------|
| **Business logic** | When the request has **only** `location` (no cuisine, budget, or min rating), Phase 2 does not constrain cuisine/budget/rating. `phase4/service.py` (`_location_only_preferences`) sets LLM `top_n` to `min(shortlist length, max_shortlist_candidates)` so every shortlisted row can receive a ranked explanation (up to the shortlist cap). |

---

## 6. Cuisine from dataset only + fuzzy match

| Layer | Details |
|--------|---------|
| **Backend** | `GET /api/v1/cuisines` returns distinct comma-split tokens from the `cuisines` column only (`phase2/cuisine_catalog.py`). Invalid cuisine vs dataset returns **422**. |
| **Business logic** | `phase2/selection.py` resolves user cuisine against catalog tokens; fuzzy matching where configured. |
| **Frontend** | `phase4/web`: cuisine suggestions from `/api/v1/cuisines`; submits resolved preference to `POST /api/v1/recommendations`. |

---

## 7. UI behavior (Next.js)

| Layer | Details |
|--------|---------|
| **Frontend** | (`phase4/web`) Hero, filters, “Personalized Picks” cards with AI explanations; errors surfaced in the UI. Next rewrites same-origin API paths to the Python backend (no extra CORS setup for local dev). |

---

## 8. De-duplication

| Layer | Details |
|--------|---------|
| **Business logic** | Phase 2 de-duplicates candidate venues before the LLM; merge layer in `phase4/service.py` preserves one row per venue where applicable. |

---

## 9. Response metadata

| Layer | Details |
|--------|---------|
| **Backend** | Responses include `explanation` per pick, optional `degraded` / `message`, and `meta` such as `cuisine_resolved`. `HTTPException` (e.g. **422**) is not swallowed by generic **503** handlers. |

---

## Document control

| Field | Value |
|-------|--------|
| Related | [architecture.md](./architecture.md) |
| Purpose | Track implemented improvements and code mapping |

When behavior changes, update this file and **architecture.md** together.
