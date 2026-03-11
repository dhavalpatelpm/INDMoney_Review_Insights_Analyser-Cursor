"""
Theme classification: assign each review to one theme from the list (Groq, batched).
Fallback theme "Other" for low-confidence or irrelevant.
Runs batches in parallel when max_workers > 1.
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_SIZE = 50
FALLBACK_THEME = "Other"


def _load_prompts() -> dict:
    import yaml
    path = PROJECT_ROOT / "config" / "prompts.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _normalize_for_match(s: str) -> str:
    """Normalize string for flexible matching: lowercase, collapse punctuation/whitespace."""
    s = re.sub(r"[\s/_\-]+", " ", s.lower().strip())
    return " ".join(s.split())


def _best_match_theme(line: str, theme_set: set[str]) -> str:
    """Map LLM output to a theme. Exact match first, then flexible (ignoring /, -, spaces)."""
    allowed = {t.strip(): t for t in theme_set}
    key_normalized = {_normalize_for_match(t): t for t in theme_set}
    line_clean = re.sub(r"^[\d\.\)\-\*]+\s*", "", line.strip()).strip()
    if not line_clean:
        return FALLBACK_THEME
    # Exact match (case-insensitive)
    if line_clean in allowed:
        return allowed[line_clean]
    key_lower = line_clean.lower()
    if key_lower in {t.lower() for t in theme_set}:
        for t in theme_set:
            if t.lower() == key_lower:
                return t
    # Flexible: normalize both (ignore / - _ and spacing) and compare
    norm_line = _normalize_for_match(line_clean)
    if norm_line in key_normalized:
        return key_normalized[norm_line]
    # Word-overlap: "Transaction Charges" -> "Transaction/Charges"
    words_line = set(norm_line.split())
    for norm, canonical in key_normalized.items():
        words_theme = set(norm.split())
        if words_line == words_theme or (len(words_line) >= 2 and words_theme <= words_line):
            return canonical
    return FALLBACK_THEME


def _parse_theme_lines(response: str, theme_set: set[str], count: int) -> list[str]:
    """Parse response into one theme per line; map to theme_set or Other (flexible matching)."""
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    result = [_best_match_theme(line, theme_set) for line in lines]
    return result[:count]


def _classify_batch(
    batch: list[dict[str, Any]],
    batch_idx: int,
    themes: list[str],
    theme_set: set[str],
    client: Any,
    prompts_cfg: dict,
    text_key: str,
    model: str | None,
) -> tuple[int, list[dict[str, Any]]]:
    """Classify one batch; returns (batch_idx, list of reviews with theme)."""
    system = prompts_cfg.get(
        "system",
        "You assign exactly one theme to each review. Reply with only the theme name from the list, one per line.",
    )
    user_prefix_tpl = prompts_cfg.get(
        "user_prefix",
        "Themes: {themes}\n\nFor each review below, reply with exactly one theme from the list. If none fit, reply Other. One theme per line, same order as reviews.\n\nReviews:\n",
    )
    from phase2.groq_client import chat, DEFAULT_MODEL
    theme_list_str = "\n".join(f"- {t}" for t in themes)
    themes_comma = ", ".join(themes)
    review_lines = []
    for r in batch:
        t = (r.get(text_key) or "").strip()
        if len(t) > 250:
            t = t[:247] + "..."
        review_lines.append(t or "(no text)")
    format_vars = {"themes": themes_comma, "themes_list": theme_list_str}
    user_content = user_prefix_tpl.format(**format_vars) + "\n" + "\n".join(f"{j+1}. {t}" for j, t in enumerate(review_lines))
    out = []
    try:
        response = chat(client, system, user_content, model=model or DEFAULT_MODEL)
        assigned = _parse_theme_lines(response, theme_set, len(batch))
        for k, rev in enumerate(batch):
            rev = dict(rev)
            rev["theme"] = assigned[k] if k < len(assigned) else FALLBACK_THEME
            out.append(rev)
    except Exception as e:
        logger.warning("Classification batch %s failed: %s; assigning Other", batch_idx, e)
        for rev in batch:
            rev = dict(rev)
            rev["theme"] = FALLBACK_THEME
            out.append(rev)
    return batch_idx, out


def classify_reviews(
    reviews: list[dict[str, Any]],
    themes: list[str],
    client: Any,
    batch_size: int = BATCH_SIZE,
    text_key: str = "text",
    model: str | None = None,
    max_workers: int = 1,
) -> list[dict[str, Any]]:
    """
    Assign one theme to each review using Groq (batched). Adds "theme" key to each review.
    Runs batches in parallel when max_workers > 1. Returns list of reviews with "theme" set.
    """
    if not themes or not reviews:
        for r in reviews:
            r["theme"] = FALLBACK_THEME
        return reviews
    theme_set = set(themes) | {FALLBACK_THEME}
    prompts_cfg = _load_prompts().get("theme_classification", {})
    used_model = model

    batches = []
    for i in range(0, len(reviews), batch_size):
        batches.append((i // batch_size, reviews[i : i + batch_size]))

    if max_workers <= 1 or len(batches) <= 1:
        out = []
        for idx, batch in batches:
            _, classified = _classify_batch(
                batch, idx, themes, theme_set, client, prompts_cfg, text_key, used_model
            )
            out.extend(classified)
        return out

    results: dict[int, list[dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _classify_batch, batch, idx, themes, theme_set, client, prompts_cfg, text_key, used_model
            ): idx
            for idx, batch in batches
        }
        for future in as_completed(futures):
            batch_idx, classified = future.result()
            results[batch_idx] = classified

    out = []
    for idx in sorted(results.keys()):
        out.extend(results[idx])
    return out
