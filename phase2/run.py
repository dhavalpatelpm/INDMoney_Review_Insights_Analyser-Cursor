"""
Phase 2 orchestration: load cleaned reviews -> discover themes (Groq) -> classify (Groq) -> group -> save.
Requires GROQ_API_KEY in environment (or in .env via python-dotenv).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Optional: load .env so GROQ_API_KEY can be set in .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from phase2.classify import classify_reviews
from phase2.discover import discover_themes
from phase2.groq_client import get_client
from phase2.grouping import theme_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    import yaml
    config_path = PROJECT_ROOT / "config" / "settings.yaml"
    if not config_path.exists():
        return _default_config()
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or _default_config()


def _default_config() -> dict:
    return {
        "data_dir": "data",
        "cleaned_reviews_file": "cleaned_reviews.json",
        "themed_reviews_file": "themed_reviews.json",
        "max_themes": 5,
        "theme_discovery_use_all_reviews": False,
        "theme_discovery_sample_size": 80,
        "theme_discovery_chunk_size": 0,
        "theme_classification_batch_size": 50,
        "theme_classification_max_workers": 3,
    }


def load_cleaned_reviews(data_dir: Path, cleaned_file: str) -> list[dict]:
    path = data_dir / cleaned_file
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_themed(themed: dict, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(themed, f, ensure_ascii=False, indent=2)
    logger.info("Saved themed output to %s", filepath)


def run_phase2(config: dict | None = None) -> dict:
    """
    Run Phase 2: load cleaned reviews -> discover 3-5 themes (Groq) -> classify each review (Groq) -> group and rank.
    Returns structured output: themes, groups, theme_rank, reviews_with_themes.
    """
    cfg = config or load_config()
    data_dir = PROJECT_ROOT / cfg.get("data_dir", "data")
    cleaned_file = cfg.get("cleaned_reviews_file", "cleaned_reviews.json")
    themed_file = cfg.get("themed_reviews_file", "themed_reviews.json")
    max_themes = int(cfg.get("max_themes", 5))
    use_all_reviews = cfg.get("theme_discovery_use_all_reviews", True)
    chunk_size = int(cfg.get("theme_discovery_chunk_size", 0))  # 0 = single request
    chunk_delay = float(cfg.get("theme_discovery_chunk_delay_seconds", 1.0))
    batch_size = int(cfg.get("theme_classification_batch_size", 50))
    max_workers = int(cfg.get("theme_classification_max_workers", 1))

    reviews = load_cleaned_reviews(data_dir, cleaned_file)
    sample_size = len(reviews) if use_all_reviews else int(cfg.get("theme_discovery_sample_size", 150))
    if not reviews:
        logger.warning("No cleaned reviews found at %s/%s. Run Phase 1 first.", data_dir, cleaned_file)
        return {"themes": [], "groups": {}, "theme_rank": [], "reviews_with_themes": []}

    logger.info("Phase 2: Loaded %s cleaned reviews", len(reviews))
    client = get_client()

    logger.info("Phase 2: Discovering themes (Groq) using %s reviews (chunk_size=%s)", sample_size, chunk_size or "single")
    themes = discover_themes(
        reviews, client,
        max_themes=max_themes,
        sample_size=sample_size,
        chunk_size=chunk_size,
        chunk_delay_seconds=chunk_delay,
    )
    logger.info("Discovered themes: %s", themes)

    logger.info("Phase 2: Classifying reviews (Groq, batch size %s, workers %s)", batch_size, max_workers)
    reviews_with_themes = classify_reviews(
        reviews, themes, client, batch_size=batch_size, max_workers=max_workers
    )

    groups, theme_rank = theme_summary(reviews_with_themes)
    logger.info("Phase 2: Grouped into %s themes; rank: %s", len(groups), theme_rank)

    # Build output: theme -> list of {review_id, text, rating, date} (no PII)
    groups_serializable = {}
    for theme, revs in groups.items():
        groups_serializable[theme] = [
            {"review_id": r.get("review_id"), "text": r.get("text"), "rating": r.get("rating"), "date": r.get("date")}
            for r in revs
        ]

    themed = {
        "themes": themes,
        "theme_rank": theme_rank,
        "groups": groups_serializable,
        "reviews_with_themes": [
            {"review_id": r.get("review_id"), "text": r.get("text"), "rating": r.get("rating"), "date": r.get("date"), "theme": r.get("theme")}
            for r in reviews_with_themes
        ],
    }
    save_themed(themed, data_dir / themed_file)
    return themed


def main() -> int:
    run_phase2()
    return 0


if __name__ == "__main__":
    sys.exit(main())
