"""
Phase 1 orchestration: fetch -> save raw -> clean -> English only -> no emoji/slang -> min 5 words -> redact -> save cleaned.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from phase1.clean import clean_reviews, filter_by_min_words
from phase1.content_filter import filter_no_emoji_no_slang
from phase1.fetcher import fetch_reviews
from phase1.language_filter import filter_english_only
from phase1.redact import redact_reviews
from phase1.storage import save_cleaned_reviews, save_raw_reviews

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
        "app_id": "in.indwealth",
        "weeks_back": 12,
        "lang": "en",
        "country": "in",
        "data_dir": "data",
        "raw_reviews_file": "raw_reviews.json",
        "cleaned_reviews_file": "cleaned_reviews.json",
        "reviews_per_request": 200,
        "request_delay_seconds": 1,
        "max_retries": 3,
    }


def run_phase1(config: dict | None = None) -> tuple[list[dict], list[dict]]:
    """
    Run Phase 1: fetch -> save raw -> clean -> English only -> no emoji/slang -> min 5 words -> redact -> save cleaned.
    Returns (raw_reviews, cleaned_reviews).
    """
    cfg = config or load_config()
    data_dir = PROJECT_ROOT / cfg.get("data_dir", "data")
    raw_path = data_dir / cfg.get("raw_reviews_file", "raw_reviews.json")
    cleaned_path = data_dir / cfg.get("cleaned_reviews_file", "cleaned_reviews.json")

    logger.info("Phase 1: Fetching reviews for %s (last %s weeks)", cfg["app_id"], cfg["weeks_back"])
    raw = fetch_reviews(
        app_id=cfg["app_id"],
        weeks_back=int(cfg.get("weeks_back", 12)),
        lang=cfg.get("lang", "en"),
        country=cfg.get("country", "in"),
        count_per_request=int(cfg.get("reviews_per_request", 200)),
        delay_seconds=float(cfg.get("request_delay_seconds", 1.0)),
        max_retries=int(cfg.get("max_retries", 3)),
    )
    logger.info("Fetched %s reviews", len(raw))
    if not raw:
        logger.warning("No reviews fetched. Check app_id and network.")
        return [], []

    save_raw_reviews(raw, raw_path)

    logger.info("Phase 1: Cleaning, filtering (English, no emoji/slang, min 5 words), and redacting")
    cleaned = clean_reviews(raw)
    before_lang = len(cleaned)
    cleaned = filter_english_only(cleaned)
    logger.info("Filtered out %s non-English reviews", before_lang - len(cleaned))
    before_content = len(cleaned)
    cleaned = filter_no_emoji_no_slang(cleaned)
    logger.info("Filtered out %s reviews with emoji or slang", before_content - len(cleaned))
    before_words = len(cleaned)
    cleaned = filter_by_min_words(cleaned, min_words=5)
    logger.info("Filtered out %s reviews with fewer than 5 words", before_words - len(cleaned))
    cleaned = redact_reviews(cleaned)
    save_cleaned_reviews(cleaned, cleaned_path)

    return raw, cleaned


def main() -> int:
    run_phase1()
    return 0


if __name__ == "__main__":
    sys.exit(main())
