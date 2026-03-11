"""
Text cleaning: normalise encoding, trim, collapse whitespace.
Filter out reviews with fewer than min_words in the body.
Title is not used; it is omitted from the output.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

DEFAULT_MIN_WORDS = 5


def clean_text(text: str | None) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        return str(text)
    s = unicodedata.normalize("NFC", text)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _word_count(text: str) -> int:
    return len(clean_text(text).split()) if text else 0


def clean_review(review: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with text cleaned and title removed (not required)."""
    out = {k: v for k, v in review.items() if k != "title"}
    out["text"] = clean_text(review.get("text"))
    return out


def clean_reviews(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clean all reviews (no title in output)."""
    return [clean_review(r) for r in reviews]


def filter_by_min_words(
    reviews: list[dict[str, Any]],
    min_words: int = DEFAULT_MIN_WORDS,
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """Keep only reviews whose text has at least min_words words."""
    return [r for r in reviews if _word_count(r.get(text_key)) >= min_words]
