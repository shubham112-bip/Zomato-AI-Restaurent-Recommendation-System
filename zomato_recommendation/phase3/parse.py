"""Extract and validate LLM JSON (architecture §5.3)."""

from __future__ import annotations

import json
import re
from typing import Any

from zomato_recommendation.phase3.schemas import LlmPayload


def _strip_markdown_json_fence(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```\s*$", t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


def parse_llm_json(content: str) -> LlmPayload:
    """Parse model output into ``LlmPayload``; raises ``ValueError`` if invalid."""
    raw = _strip_markdown_json_fence(content)
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return LlmPayload.model_validate(data)
