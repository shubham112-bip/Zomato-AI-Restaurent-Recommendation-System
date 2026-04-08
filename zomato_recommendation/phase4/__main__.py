"""Run the Phase 4 JSON HTTP API: ``python -m zomato_recommendation.phase4`` (Uvicorn)."""

from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        "zomato_recommendation.phase4.app:app",
        host=host,
        port=port,
        reload=os.getenv("API_RELOAD", "").lower() in ("1", "true", "yes"),
    )
