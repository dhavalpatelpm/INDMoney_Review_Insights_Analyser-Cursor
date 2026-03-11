"""
Action ideas: use Gemini to suggest 3 concrete, prioritised actions from top themes and quotes.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_prompt() -> str:
    import yaml
    path = PROJECT_ROOT / "config" / "prompts.yaml"
    if not path.exists():
        return "Suggest exactly 3 action ideas, one per line: {themes}\n{quotes}"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("action_ideas", {}).get("prompt", "Suggest 3 action ideas, one per line.\nThemes: {themes}\nQuotes: {quotes}")


def generate_actions(
    client: Any,
    top_themes: list[str],
    quotes: list[dict[str, Any]],
    actions_count: int = 3,
    model: str | None = None,
) -> list[str]:
    """
    Call Gemini to get actions_count action ideas. Returns list of action strings.
    """
    themes_str = ", ".join(top_themes)
    quotes_str = "\n".join(f"- [{q.get('theme', '')}] {q.get('text', '')}" for q in quotes)
    tpl = _load_prompt()
    prompt = tpl.format(themes=themes_str, quotes=quotes_str)
    from phase3.gemini_client import generate_text, DEFAULT_MODEL
    response = generate_text(client, prompt, model=model or DEFAULT_MODEL)
    actions = []
    for line in response.splitlines():
        line = re.sub(r"^[\d\.\)\-\*]+\s*", "", line.strip()).strip()
        if line and len(actions) < actions_count:
            actions.append(line)
    return actions[:actions_count]
