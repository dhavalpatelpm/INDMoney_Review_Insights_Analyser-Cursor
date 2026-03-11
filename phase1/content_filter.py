"""
Filter out reviews that contain emoji or slang words.
Keeps only reviews with no emoji and no slang.
"""
from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Emoji detection: regex covering common emoji ranges (no extra dependency)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U0001F900-\U0001F9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"  # chess, symbols
    "]+",
    flags=re.UNICODE,
)


# Slang / informal words (lowercase, word-boundary match). Avoid normal words.
SLANG_WORDS = frozenset({
    "lol", "lmao", "lmfao", "omg", "omfg", "btw", "idk", "imo", "imho",
    "tbh", "gonna", "wanna", "gotta", "kinda", "sorta", "coulda", "shoulda",
    "woulda", "dunno", "yep", "nope", "nah", "meh", "yup",
    "plz", "pls", "thx", "ty", "np", "nvm", "nm",
    "wtf", "wth", "asap", "fyi", "rn", "atm", "irl",
    "cuz", "cos", "coz", "bcoz", "bc",
    "dude", "bro", "bruh", "sis", "fam", "lit", "vibes", "vibe",
    "kk", "yea", "gud", "gr8", "awsm", "tho", "thru",
    "sup", "wassup", "yo", "hii", "hiii",
    "sux", "luv", "luvs", "fav", "fave", "def", "prob",
    "smh", "idc", "idgaf", "tgif", "bae", "hmu", "tbt", "fomo", "yolo", "ftw",
    "ppl", "cmon", "gimme", "lemme",
})


def contains_emoji(text: str | None) -> bool:
    """Return True if text contains any emoji."""
    if not text or not isinstance(text, str):
        return False
    return bool(_EMOJI_PATTERN.search(text))


def contains_slang(text: str | None) -> bool:
    """Return True if text contains any slang word (whole-word match, case-insensitive)."""
    if not text or not isinstance(text, str):
        return False
    # Normalise: lowercase, split on non-letters for word boundaries
    words = re.findall(r"[a-z]+", text.lower())
    return bool(words and SLANG_WORDS.intersection(words))


def filter_no_emoji_no_slang(
    reviews: list[dict[str, Any]],
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """Keep only reviews that contain no emoji and no slang words."""
    kept = []
    dropped_emoji = 0
    dropped_slang = 0
    for r in reviews:
        text = r.get(text_key) or ""
        if contains_emoji(text):
            dropped_emoji += 1
            continue
        if contains_slang(text):
            dropped_slang += 1
            continue
        kept.append(r)
    if dropped_emoji or dropped_slang:
        logger.info(
            "Content filter: dropped %s reviews with emoji, %s with slang; kept %s",
            dropped_emoji, dropped_slang, len(kept),
        )
    return kept
