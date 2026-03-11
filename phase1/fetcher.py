"""
Fetch Google Play reviews with pagination until we have all reviews
within the configured time window (e.g. 8-12 weeks). Uses continuation_token
to get more than the default ~300 reviews.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from google_play_scraper import reviews as gplay_reviews, Sort

logger = logging.getLogger(__name__)


def _review_to_record(item: Any) -> dict[str, Any]:
    """Map google-play-scraper review object to our schema."""
    at = item.get("at")
    if hasattr(at, "isoformat"):
        date_str = at.isoformat()
    else:
        date_str = str(at) if at else ""
    return {
        "review_id": item.get("reviewId", ""),
        "rating": int(item.get("score", 0)),
        "text": (item.get("content") or "").strip(),
        "date": date_str,
        "thumbs_up": int(item.get("thumbsUpCount", 0)),
        "app_version": item.get("reviewCreatedVersion") or item.get("appVersion") or "",
    }


def fetch_reviews(
    app_id: str = "in.indwealth",
    weeks_back: int = 12,
    lang: str = "en",
    country: str = "in",
    count_per_request: int = 200,
    delay_seconds: float = 1.0,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch all reviews from the last `weeks_back` weeks using pagination.
    Stops when the oldest review in a batch is older than the cutoff date,
    or when there is no continuation token.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks_back)
    all_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    continuation_token = None
    page = 0

    while True:
        page += 1
        for attempt in range(max_retries):
            try:
                result, continuation_token = gplay_reviews(
                    app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    continuation_token=continuation_token,
                    count=count_per_request,
                )
                break
            except Exception as e:
                logger.warning("Request attempt %s failed: %s", attempt + 1, e)
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay_seconds * (attempt + 1))

        if not result:
            break

        stop_fetching = False
        for item in result:
            at = item.get("at")
            if at:
                if at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)
                if at < cutoff:
                    stop_fetching = True
                    continue
            rec = _review_to_record(item)
            if rec["review_id"] in seen_ids:
                continue
            seen_ids.add(rec["review_id"])
            all_records.append(rec)

        logger.info("Page %s: got %s reviews, total %s", page, len(result), len(all_records))

        if stop_fetching or not continuation_token:
            break

        time.sleep(delay_seconds)

    return all_records
