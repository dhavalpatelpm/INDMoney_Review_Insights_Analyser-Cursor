"""
Group reviews by assigned theme and rank themes by count.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def group_by_theme(reviews: list[dict[str, Any]], theme_key: str = "theme") -> dict[str, list[dict[str, Any]]]:
    """Group reviews by theme. Returns dict theme -> list of reviews."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in reviews:
        theme = r.get(theme_key) or "Other"
        groups[theme].append(r)
    return dict(groups)


def rank_themes(groups: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Return theme names ordered by count (descending)."""
    return [t for t, _ in sorted(groups.items(), key=lambda x: -len(x[1]))]


def theme_summary(
    reviews: list[dict[str, Any]],
    theme_key: str = "theme",
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """
    Group reviews by theme and rank themes by frequency.
    Returns (theme -> [reviews], ranked_theme_names).
    """
    groups = group_by_theme(reviews, theme_key=theme_key)
    ranked = rank_themes(groups)
    return groups, ranked
