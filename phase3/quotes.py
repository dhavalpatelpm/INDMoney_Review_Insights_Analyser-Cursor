"""
Quote selection: pick one representative quote per top theme (or 3 total). Heuristic-based.
"""
from __future__ import annotations

from typing import Any


def select_quotes(
    groups: dict[str, list[dict[str, Any]]],
    top_themes: list[str],
    quotes_count: int = 3,
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """
    Select up to quotes_count representative quotes from the top themes.
    Picks one quote per theme (prefer mid-length, impactful); if fewer themes than quotes_count, fill from next theme.
    Returns list of {theme, text} dicts.
    """
    selected = []
    for theme in top_themes:
        revs = groups.get(theme, [])
        if not revs:
            continue
        # Prefer quote with reasonable length (not too short, not too long) and with some substance
        best = _pick_best_quote(revs, text_key)
        if best:
            selected.append({"theme": theme, "text": best.get(text_key, "").strip()})
        if len(selected) >= quotes_count:
            break
    return selected[:quotes_count]


def _pick_best_quote(reviews: list[dict[str, Any]], text_key: str) -> dict[str, Any] | None:
    """Pick one review to use as quote: prefer 50-200 chars, else first with text."""
    if not reviews:
        return None
    for r in reviews:
        t = (r.get(text_key) or "").strip()
        if not t:
            continue
        n = len(t)
        if 50 <= n <= 300:
            return r
    return reviews[0]
