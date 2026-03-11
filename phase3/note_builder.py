"""
Build the one-page weekly note from top themes, quotes, and actions.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def build_note(
    top_themes: list[str],
    quotes: list[dict[str, Any]],
    actions: list[str],
    meta: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """
    Build structured note (dict) and human-readable one-page text.
    Returns (structured_note, note_text).
    """
    meta = meta or {}
    date_range = meta.get("date_range", "—")
    total_reviews = meta.get("total_reviews", 0)
    title = f"INDmoney Weekly Review Pulse — {date_range}"

    structured = {
        "title": title,
        "themes": top_themes,
        "quotes": quotes,
        "actions": actions,
        "meta": {"date_range": date_range, "total_reviews": total_reviews},
    }

    lines = [
        title,
        "",
        "--- Top themes ---",
    ]
    for i, theme in enumerate(top_themes, 1):
        lines.append(f"{i}. {theme}")
        q = next((x for x in quotes if x.get("theme") == theme), None)
        if q and q.get("text"):
            lines.append(f'   Quote: "{q["text"]}"')
        lines.append("")
    lines.append("--- Action ideas ---")
    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. {action}")
    lines.append("")
    lines.append(f"Review count: {total_reviews}  |  Period: {date_range}")
    note_text = "\n".join(lines)
    return structured, note_text


def date_range_from_reviews(reviews_or_groups: Any) -> str:
    """Compute a simple date range string from review dates if available."""
    dates = []
    if isinstance(reviews_or_groups, list):
        for r in reviews_or_groups:
            d = r.get("date") or r.get("date_iso")
            if d:
                dates.append(d[:10] if len(d) >= 10 else d)
    elif isinstance(reviews_or_groups, dict):
        for revs in reviews_or_groups.values():
            if isinstance(revs, list):
                for r in revs:
                    d = r.get("date") or r.get("date_iso")
                    if d:
                        dates.append(d[:10] if len(d) >= 10 else d)
    if not dates:
        return datetime.now().strftime("%d %b %Y")
    try:
        min_d = min(dates)
        max_d = max(dates)
        return f"{min_d} to {max_d}"
    except Exception:
        return datetime.now().strftime("%d %b %Y")
