"""Phase 4 — HTTP API (backend). Web UI is planned separately (see ``doc/architecture.md``)."""

from zomato_recommendation.phase4.app import app, create_app

__all__ = ["app", "create_app"]
