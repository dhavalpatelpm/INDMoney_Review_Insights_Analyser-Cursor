"""
Save and load raw and cleaned reviews. Deduplicate by review_id on load/save.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_raw_reviews(reviews: list[dict[str, Any]], filepath: str | Path) -> None:
    """Persist raw reviews (idempotent: overwrites)."""
    path = Path(filepath)
    _ensure_dir(path)
    by_id = {r["review_id"]: r for r in reviews}
    deduped = list(by_id.values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s raw reviews to %s", len(deduped), path)


def load_raw_reviews(filepath: str | Path) -> list[dict[str, Any]]:
    """Load raw reviews from JSON. Returns empty list if file missing."""
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_cleaned_reviews(reviews: list[dict[str, Any]], filepath: str | Path) -> None:
    """Persist cleaned (and PII-redacted) reviews."""
    path = Path(filepath)
    _ensure_dir(path)
    by_id = {r["review_id"]: r for r in reviews}
    deduped = list(by_id.values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s cleaned reviews to %s", len(deduped), path)


def load_cleaned_reviews(filepath: str | Path) -> list[dict[str, Any]]:
    """Load cleaned reviews from JSON. Returns empty list if file missing."""
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []
