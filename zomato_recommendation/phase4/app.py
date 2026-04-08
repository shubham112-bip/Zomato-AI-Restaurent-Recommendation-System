"""Phase 4 JSON HTTP API — Python backend for the Next.js UI (see doc/architecture.md §6, §10)."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException, Request

from zomato_recommendation.phase1.field_mapping import CANONICAL_COLUMNS, COL_CITY, COL_LOCATION
from zomato_recommendation.phase1.load import load_restaurants
from zomato_recommendation.phase2.cuisine_catalog import build_cuisine_catalog
from zomato_recommendation.phase4.schemas import (
    CuisinesResponse,
    LocationsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from zomato_recommendation.phase4.service import run_recommendations

logger = logging.getLogger(__name__)

api_v1 = APIRouter(prefix="/api/v1", tags=["v1"])


def _empty_canonical_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(CANONICAL_COLUMNS))


def _distinct_catalog_locations(df: pd.DataFrame) -> list[str]:
    """All distinct non-empty city and neighborhood strings in the loaded catalog (case-insensitive dedupe)."""
    seen_ci: set[str] = set()
    out: list[str] = []
    for col in (COL_CITY, COL_LOCATION):
        if col not in df.columns:
            continue
        for raw in df[col].dropna().astype(str).str.strip():
            if not raw:
                continue
            key = raw.casefold()
            if key in seen_ci:
                continue
            seen_ci.add(key)
            out.append(raw)
    out.sort(key=lambda s: s.casefold())
    return out


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.df = _empty_canonical_frame()
    app.state.dataset_ready = True

    if os.getenv("ZOMATO_SKIP_DATASET_LOAD", "").lower() in ("1", "true", "yes"):
        logger.info("ZOMATO_SKIP_DATASET_LOAD set — starting with empty dataset (tests or offline).")
        yield
        return

    max_rows_raw = os.getenv("ZOMATO_MAX_ROWS", "8000")
    try:
        max_rows = int(max_rows_raw)
    except ValueError:
        max_rows = 8000

    app.state.dataset_ready = False
    logger.info("Loading Hugging Face dataset in background (max_rows=%s)…", max_rows)

    async def _load_hf() -> None:
        try:
            df = await asyncio.to_thread(load_restaurants, max_rows=max_rows)
            app.state.df = df
            logger.info("Loaded %s restaurant rows.", len(df))
        except Exception as e:
            logger.exception("Failed to load Hugging Face dataset: %s", e)
            app.state.df = _empty_canonical_frame()
        finally:
            app.state.dataset_ready = True

    asyncio.create_task(_load_hf())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Restaurant recommendations API",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health(request: Request) -> dict[str, Any]:
        ready = getattr(request.app.state, "dataset_ready", True)
        return {"status": "ok", "dataset_ready": ready}

    @app.get("/")
    async def root() -> dict[str, Any]:
        """Service descriptor — open the Next.js app in ``phase4/web`` for the product UI."""
        return {
            "service": "zomato-recommendation-api",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "ui": "Run Next.js from ``zomato_recommendation/phase4/web`` (``npm run dev``); it proxies to this API.",
        }

    async def _recommendations_handler(request: Request, body: RecommendationRequest) -> RecommendationResponse:
        if not getattr(request.app.state, "dataset_ready", True):
            raise HTTPException(
                status_code=503,
                detail="Dataset is still loading from Hugging Face. Wait up to a few minutes and retry.",
            )

        df: pd.DataFrame = request.app.state.df
        if df is None:
            raise HTTPException(status_code=503, detail="Dataset not initialized.")

        try:
            return run_recommendations(body, df)
        except HTTPException:
            raise
        except RuntimeError as e:
            msg = str(e)
            if "GROQ_API_KEY" in msg or "API key" in msg.lower():
                raise HTTPException(
                    status_code=503,
                    detail="LLM service unavailable. Configure GROQ_API_KEY / API_KEY in .env.",
                ) from e
            raise HTTPException(status_code=503, detail="Recommendation service error.") from e
        except Exception as e:
            logger.exception("Recommendation failed")
            raise HTTPException(
                status_code=503,
                detail="Recommendation failed. Try again later.",
            ) from e

    @app.post("/v1/recommendations", response_model=RecommendationResponse)
    async def post_recommendations_v1_legacy(
        body: RecommendationRequest,
        request: Request,
    ) -> RecommendationResponse:
        return await _recommendations_handler(request, body)

    @api_v1.get("/locations", response_model=LocationsResponse)
    async def list_locations(request: Request) -> LocationsResponse:
        if not getattr(request.app.state, "dataset_ready", True):
            raise HTTPException(
                status_code=503,
                detail="Dataset is still loading from Hugging Face. Wait up to a few minutes and retry.",
            )
        df: pd.DataFrame = request.app.state.df
        if df is None or len(df) == 0:
            return LocationsResponse(locations=[])
        return LocationsResponse(locations=_distinct_catalog_locations(df))

    @api_v1.get("/cuisines", response_model=CuisinesResponse)
    async def list_cuisines(request: Request) -> CuisinesResponse:
        if not getattr(request.app.state, "dataset_ready", True):
            raise HTTPException(
                status_code=503,
                detail="Dataset is still loading from Hugging Face. Wait up to a few minutes and retry.",
            )
        df: pd.DataFrame = request.app.state.df
        if df is None:
            df = _empty_canonical_frame()
        return CuisinesResponse(cuisines=build_cuisine_catalog(df))

    @api_v1.post("/recommendations", response_model=RecommendationResponse)
    async def post_recommendations_v1(
        body: RecommendationRequest,
        request: Request,
    ) -> RecommendationResponse:
        return await _recommendations_handler(request, body)

    app.include_router(api_v1)

    return app


app = create_app()
