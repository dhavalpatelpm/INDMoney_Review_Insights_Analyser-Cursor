"""
Phase 3 orchestration: load themed reviews -> top 3 themes -> select 3 quotes -> Gemini action ideas -> build one-page note -> save.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from phase3.actions import generate_actions
from phase3.gemini_client import get_client
from phase3.note_builder import build_note, date_range_from_reviews
from phase3.quotes import select_quotes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    import yaml
    path = PROJECT_ROOT / "config" / "settings.yaml"
    if not path.exists():
        return _default_config()
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or _default_config()


def _default_config() -> dict:
    return {
        "data_dir": "data",
        "themed_reviews_file": "themed_reviews.json",
        "weekly_notes_dir": "weekly_notes",
        "weekly_note_filename": "weekly_note",
        "top_themes_count": 3,
        "quotes_count": 3,
        "actions_count": 3,
    }


def load_themed_reviews(data_dir: Path, themed_file: str) -> dict:
    path = data_dir / themed_file
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_phase3(config: dict | None = None) -> dict:
    """
    Run Phase 3: load themed_reviews.json -> top 3 themes -> 3 quotes -> Gemini 3 actions -> one-page note.
    Returns structured note dict.
    """
    cfg = config or load_config()
    data_dir = PROJECT_ROOT / cfg.get("data_dir", "data")
    themed_file = cfg.get("themed_reviews_file", "themed_reviews.json")
    notes_dir = data_dir / cfg.get("weekly_notes_dir", "weekly_notes")
    note_filename = cfg.get("weekly_note_filename", "weekly_note")
    top_n = int(cfg.get("top_themes_count", 3))
    quotes_count = int(cfg.get("quotes_count", 3))
    actions_count = int(cfg.get("actions_count", 3))

    themed = load_themed_reviews(data_dir, themed_file)
    if not themed:
        logger.warning("No themed reviews at %s/%s. Run Phase 2 first.", data_dir, themed_file)
        return {}

    theme_rank = themed.get("theme_rank", [])
    groups = themed.get("groups", {})
    top_themes = [t for t in theme_rank if t != "Other"][:top_n]
    if len(top_themes) < top_n and "Other" in theme_rank:
        top_themes = theme_rank[:top_n]

    total_reviews = sum(len(revs) for revs in groups.values())
    date_range = date_range_from_reviews(groups)

    logger.info("Phase 3: Top themes: %s", top_themes)
    quotes = select_quotes(groups, top_themes, quotes_count=quotes_count)
    logger.info("Phase 3: Selected %s quotes", len(quotes))

    client = get_client()
    logger.info("Phase 3: Generating action ideas (Gemini)")
    actions = generate_actions(client, top_themes, quotes, actions_count=actions_count)
    logger.info("Phase 3: Got %s actions", len(actions))

    meta = {"date_range": date_range, "total_reviews": total_reviews}
    structured, note_text = build_note(top_themes, quotes, actions, meta)

    notes_dir.mkdir(parents=True, exist_ok=True)
    json_path = notes_dir / f"{note_filename}.json"
    txt_path = notes_dir / f"{note_filename}.txt"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(note_text)
    logger.info("Phase 3: Saved note to %s and %s", json_path, txt_path)
    return structured


def main() -> int:
    run_phase3()
    return 0


if __name__ == "__main__":
    sys.exit(main())
