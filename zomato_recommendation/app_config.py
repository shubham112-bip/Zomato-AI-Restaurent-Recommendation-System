"""Load ``config.yaml`` from the repository root (defaults if missing)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG = _REPO_ROOT / "config.yaml"


@dataclass(frozen=True)
class AppConfig:
    max_shortlist_candidates: int
    top_n: int


def _deep_get(data: dict[str, Any], path: str, default: Any) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


@lru_cache
def get_app_config(path: str | Path | None = None) -> AppConfig:
    """Load YAML config; fall back to documented defaults."""
    p = Path(path) if path else _DEFAULT_CONFIG
    data: dict[str, Any] = {}
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            if isinstance(raw, dict):
                data = raw

    max_short = int(_deep_get(data, "filter.max_shortlist_candidates", 40))
    top_n = int(_deep_get(data, "recommendations.top_n", 5))
    max_short = max(1, min(max_short, 500))
    top_n = max(1, min(top_n, 50))
    return AppConfig(max_shortlist_candidates=max_short, top_n=top_n)
