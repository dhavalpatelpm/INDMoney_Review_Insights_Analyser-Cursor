"""
Keep only English-language reviews. Uses langdetect for language detection.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0  # reproducible results
except ImportError:
    detect = None  # type: ignore[assignment]


def is_english(text: str | None) -> bool:
    """Return True if text is detected as English. Short/empty text is treated as non-English."""
    if not text or not text.strip():
        return False
    if detect is None:
        logger.warning("langdetect not installed; skipping language filter")
        return True
    try:
        return detect(text) == "en"
    except Exception:
        return False


def filter_english_only(
    reviews: list[dict[str, Any]],
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """Keep only reviews whose text is detected as English."""
    if detect is None:
        return reviews
    kept = []
    for r in reviews:
        if is_english(r.get(text_key)):
            kept.append(r)
    return kept
