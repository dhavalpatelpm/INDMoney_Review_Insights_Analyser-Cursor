"""
Quote selection: pick one representative quote per top theme (or 3 total). Heuristic-based.
When all reviews are in "Other", distributes quotes from Other across the given themes.
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
    When only "Other" exists in groups (e.g. classification fallback), picks diverse quotes from Other and assigns one per theme.
    Returns list of {theme, text} dicts.
    """
    # When classification put everything in Other but we're showing discovered themes, pick quotes from Other bucket
    only_other_bucket = set(groups.keys()) <= {"Other"} and groups.get("Other") and top_themes
    if only_other_bucket:
        return _quotes_from_other_bucket(groups["Other"], top_themes, quotes_count, text_key)

    selected = []
    for theme in top_themes:
        revs = groups.get(theme, [])
        if not revs:
            continue
        best = _pick_best_quote(revs, text_key)
        if best:
            selected.append({"theme": theme, "text": best.get(text_key, "").strip()})
        if len(selected) >= quotes_count:
            break
    return selected[:quotes_count]


def _quotes_from_other_bucket(
    other_reviews: list[dict[str, Any]],
    themes: list[str],
    quotes_count: int,
    text_key: str,
) -> list[dict[str, Any]]:
    """When all reviews are in Other, pick one quote per theme from the pool (diverse selection)."""
    candidates = [r for r in other_reviews if (r.get(text_key) or "").strip()]
    if not candidates or not themes:
        return []
    selected = []
    step = max(1, len(candidates) // quotes_count) if candidates else 1
    for i in range(quotes_count):
        theme = themes[i % len(themes)]
        idx = min(i * step, len(candidates) - 1)
        r = candidates[idx]
        text = (r.get(text_key) or "").strip()
        if text:
            selected.append({"theme": theme, "text": text})
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
