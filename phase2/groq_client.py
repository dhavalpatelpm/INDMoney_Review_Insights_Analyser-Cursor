"""
Groq API client. Uses GROQ_API_KEY from environment.
"""
from __future__ import annotations

import os
from typing import Any

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[misc, assignment]

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_client() -> Any:
    """Return Groq client. Raises if groq not installed or GROQ_API_KEY missing."""
    if Groq is None:
        raise RuntimeError("Install groq: pip install groq")
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY in environment")
    return Groq(api_key=api_key)


def chat(client: Any, system: str, user: str, model: str = DEFAULT_MODEL) -> str:
    """Single non-streaming chat completion. Returns assistant content."""
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
        temperature=0.2,
    )
    return (completion.choices[0].message.content or "").strip()
