"""
Theme discovery: use Groq to suggest 3-5 thematic labels from reviews.
Can send all reviews in a single request or split into multiple requests (chunks), then merge.
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_THEMES = 5
DEFAULT_SAMPLE_SIZE = 150  # used only when not sending all reviews
MAX_CHARS_PER_REVIEW = 300


def _load_prompts() -> dict:
    import yaml
    path = PROJECT_ROOT / "config" / "prompts.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _review_texts_sample(reviews: list[dict[str, Any]], sample_size: int, text_key: str = "text") -> list[str]:
    """Return review texts for theme discovery. Trimmed per review for context."""
    n = min(sample_size, len(reviews)) if sample_size else len(reviews)
    texts = []
    for r in reviews[:n]:
        t = (r.get(text_key) or "").strip()
        if t:
            if len(t) > MAX_CHARS_PER_REVIEW:
                t = t[: MAX_CHARS_PER_REVIEW - 3] + "..."
            texts.append(t)
    return texts


def _parse_theme_lines(response: str, max_themes: int = 10) -> list[str]:
    """Parse LLM response into list of theme names (one per line)."""
    themes = []
    for line in response.splitlines():
        line = re.sub(r"^[\d\.\)\-\*]+\s*", "", line.strip()).strip()
        if line and len(themes) < max_themes:
            themes.append(line)
    return themes


def discover_themes(
    reviews: list[dict[str, Any]],
    client: Any,
    max_themes: int = DEFAULT_MAX_THEMES,
    sample_size: int | None = None,
    chunk_size: int = 0,
    chunk_delay_seconds: float = 1.0,
    model: str | None = None,
) -> list[str]:
    """
    Use Groq to suggest 3-5 theme labels from reviews.
    - If chunk_size > 0 and there are more than chunk_size reviews: send in multiple requests (chunks),
      get theme suggestions per chunk, then one merge request to produce final 3-5 themes.
    - Otherwise: single request with all (or sample of) reviews.
    Returns list of theme name strings.
    """
    if not reviews:
        return []
    n = sample_size if sample_size is not None else len(reviews)
    texts = _review_texts_sample(reviews, n)
    if not texts:
        return ["Other"]

    from phase2.groq_client import chat, DEFAULT_MODEL
    used_model = model or DEFAULT_MODEL
    prompts_cfg = _load_prompts().get("theme_discovery", {})
    system = prompts_cfg.get("system", "You are an analyst. Output only thematic labels, no explanation.")
    user_prefix = prompts_cfg.get(
        "user_prefix",
        "Given these app review excerpts (one per line), suggest 3 to 5 distinct thematic labels. Return only the theme names, one per line, no numbering.",
    )

    # Multi-request: chunk reviews, get themes per chunk, then merge
    if chunk_size > 0 and len(texts) > chunk_size:
        all_suggested = []
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i : i + chunk_size]
            user_content = user_prefix + "\n\n" + "\n".join(f"- {t}" for t in chunk)
            try:
                response = chat(client, system, user_content, model=used_model)
                suggested = _parse_theme_lines(response, max_themes=8)
                all_suggested.extend(suggested)
                logger.info("Theme discovery chunk %s: got %s suggestions (%s reviews)", i // chunk_size + 1, len(suggested), len(chunk))
            except Exception as e:
                logger.warning("Theme discovery chunk failed: %s", e)
            if i + chunk_size < len(texts) and chunk_delay_seconds > 0:
                time.sleep(chunk_delay_seconds)
        if not all_suggested:
            return ["Other"]
        merge_cfg = _load_prompts().get("theme_discovery_merge", {})
        merge_system = merge_cfg.get("system", "You are an analyst. Output only the final theme names, no explanation.")
        merge_prefix = merge_cfg.get(
            "user_prefix",
            "Merge the following theme suggestions into 3 to 5 distinct final theme names. Return only the final theme names, one per line.\n\nSuggested themes:\n",
        )
        merge_content = merge_prefix + "\n".join(f"- {t}" for t in all_suggested)
        response = chat(client, merge_system, merge_content, model=used_model)
        themes = _parse_theme_lines(response, max_themes=max_themes)
        if not themes:
            themes = ["Other"]
        return themes[:max_themes]

    # Single request
    user_content = user_prefix + "\n\n" + "\n".join(f"- {t}" for t in texts)
    response = chat(client, system, user_content, model=used_model)
    themes = _parse_theme_lines(response, max_themes=max_themes)
    if not themes:
        themes = ["Other"]
    return themes[:max_themes]
