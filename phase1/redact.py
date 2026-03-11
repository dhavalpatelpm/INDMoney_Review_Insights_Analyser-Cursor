"""
PII redaction: emails, phone numbers, names (basic patterns).
Do not include PII in outputs or send to LLM.
"""
from __future__ import annotations

import re
from typing import Any

REDACT_EMAIL = "[EMAIL_REDACTED]"
REDACT_PHONE = "[PHONE_REDACTED]"

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"(?:\+91[\s-]*)?(?:\d[\s.-]*){10,}\d"
    r"|(?:\+\d{1,3}[\s-]*)?(?:\d[\s.-]*){10,}\d",
)


def redact_text(text: str | None) -> str:
    if not text or not isinstance(text, str):
        return text or ""
    s = text
    s = EMAIL_PATTERN.sub(REDACT_EMAIL, s)
    s = PHONE_PATTERN.sub(REDACT_PHONE, s)
    return s


def redact_review(review: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with text redacted. Title is omitted (not required)."""
    out = {k: v for k, v in review.items() if k != "title"}
    out["text"] = redact_text(review.get("text"))
    return out


def redact_reviews(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Redact PII in all reviews."""
    return [redact_review(r) for r in reviews]
