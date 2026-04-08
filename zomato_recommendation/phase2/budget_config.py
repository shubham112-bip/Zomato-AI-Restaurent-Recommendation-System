"""Load and query INR budget bands (architecture §4.3)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

BudgetName = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class BudgetBandsConfig:
    """Numeric ranges for low / medium / high (cost for two, INR)."""

    low: tuple[float, float]
    medium: tuple[float, float]
    high: tuple[float, float]

    def range_for(self, band: BudgetName) -> tuple[float, float]:
        return getattr(self, band)

    def cost_in_band(self, cost: float, band: BudgetName) -> bool:
        lo, hi = self.range_for(band)
        return lo <= cost <= hi

    def cost_in_any(self, cost: float, bands: tuple[BudgetName, ...]) -> bool:
        return any(self.cost_in_band(cost, b) for b in bands)


def load_budget_bands(path: str | Path | None = None) -> BudgetBandsConfig:
    """Load JSON config; default: ``phase2/config/budget_bands.json`` in the package."""
    if path is None:
        text = resources.files("zomato_recommendation").joinpath("phase2/config/budget_bands.json").read_text(
            encoding="utf-8"
        )
        data = json.loads(text)
    else:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    bands = data["bands"]
    return BudgetBandsConfig(
        low=(float(bands["low"]["min"]), float(bands["low"]["max"])),
        medium=(float(bands["medium"]["min"]), float(bands["medium"]["max"])),
        high=(float(bands["high"]["min"]), float(bands["high"]["max"])),
    )


def allowed_budget_groups(user_band: BudgetName, relax_step: int) -> tuple[BudgetName, ...] | None:
    """
    Map architecture 'relax budget one step' to allowed bands.

    ``relax_step`` 0 = user band only; higher values widen; ``None`` return means no budget filter.
    """
    if relax_step <= 0:
        return (user_band,)
    if relax_step == 1:
        if user_band == "low":
            return ("low", "medium")
        if user_band == "medium":
            return ("low", "medium", "high")
        return ("medium", "high")
    if relax_step == 2:
        return ("low", "medium", "high")
    return None
