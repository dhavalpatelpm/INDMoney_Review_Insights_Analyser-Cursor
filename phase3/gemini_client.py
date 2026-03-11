"""
Gemini API client for Phase 3 (Weekly Note). Uses GOOGLE_API_KEY or GEMINI_API_KEY from environment.
"""
from __future__ import annotations

import os
from typing import Any

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]

DEFAULT_MODEL = "gemini-2.5-flash"


def get_client() -> Any:
    """Return Gemini client. Raises if google-genai not installed or API key missing."""
    if genai is None:
        raise RuntimeError("Install Gemini SDK: pip install google-genai")
    api_key = (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY in environment (or .env)")
    return genai.Client(api_key=api_key)


def generate_text(client: Any, prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Single prompt completion. Returns generated text."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"temperature": 0.2},
    )
    return _extract_text(response)


def _extract_text(response: Any) -> str:
    """Get text from Gemini response (handles different SDK response shapes)."""
    if hasattr(response, "text") and response.text:
        return response.text.strip()
    if hasattr(response, "candidates") and response.candidates:
        c = response.candidates[0]
        if hasattr(c, "content") and c.content and hasattr(c.content, "parts"):
            for p in c.content.parts:
                if hasattr(p, "text") and p.text:
                    return p.text.strip()
    return ""
