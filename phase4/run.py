"""
Phase 4 orchestration: load latest weekly note -> build email draft -> send (or dry run).
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

from phase4.email_draft import LOGO_CID, LOGO_PATH, build_draft, build_draft_plain
from phase4.send_email import send_email

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
        "weekly_notes_dir": "weekly_notes",
        "weekly_note_filename": "weekly_note",
        "email_dry_run": True,
    }


def load_latest_note(data_dir: Path, notes_dir: str, note_filename: str) -> dict | None:
    """Load latest weekly note JSON. Returns None if not found."""
    path = data_dir / notes_dir / f"{note_filename}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_phase4(
    config: dict | None = None,
    recipient_email: str | None = None,
    recipient_name: str | None = None,
) -> tuple[str, str]:
    """
    Run Phase 4: load latest weekly note -> build draft (with optional personalization) -> send (or dry run).

    recipient_email: pass from front-end when sending; overrides config/EMAIL_TO. Required when sending
    unless email_to is in config or EMAIL_TO is set in environment.

    recipient_name: pass from front-end for personalized greeting; email body will start with "Hi, {name},"
    then the weekly pulse content. Optional; if not provided, no greeting is added.

    Returns (subject, body). If dry run, writes draft to data/weekly_notes/email_draft.html and does not send.
    """
    cfg = config or load_config()
    data_dir = PROJECT_ROOT / cfg.get("data_dir", "data")
    notes_dir = cfg.get("weekly_notes_dir", "weekly_notes")
    note_filename = cfg.get("weekly_note_filename", "weekly_note")
    dry_run = cfg.get("email_dry_run", True)
    # Recipient: caller (e.g. front-end) first, then config, then env in send_email
    to_email = (recipient_email or "").strip() or cfg.get("email_to", "").strip()
    # Name for personalization: from caller first, then config
    name = (recipient_name or "").strip() or (cfg.get("recipient_name") or "").strip()

    note = load_latest_note(data_dir, notes_dir, note_filename)
    if not note:
        logger.warning("No weekly note found at %s/%s/%s.json. Run Phase 3 first.", data_dir, notes_dir, note_filename)
        return "", ""

    subject, body = build_draft(note, recipient_name=name or None)
    logger.info("Phase 4: Draft subject: %s", subject)

    if dry_run:
        draft_dir = data_dir / notes_dir
        draft_dir.mkdir(parents=True, exist_ok=True)
        draft_path = draft_dir / "email_draft.html"
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(
                f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>'
                f'<p><strong>Subject:</strong> {subject}</p>\n\n{body}</body></html>'
            )
        _, body_plain = build_draft_plain(note, recipient_name=name or None)
        txt_path = draft_dir / "email_draft.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Subject: {subject}\n\n{body_plain}")
        logger.info("Phase 4: Dry run — draft saved to %s and %s (not sent)", draft_path, txt_path)
        return subject, body

    send_email(
        subject,
        body,
        recipient_email=to_email or None,
        logo_path=LOGO_PATH if LOGO_PATH.exists() else None,
        logo_cid=LOGO_CID,
    )
    logger.info("Phase 4: Email sent to %s", to_email or "(from env)")
    return subject, body


def main() -> int:
    run_phase4()
    return 0


if __name__ == "__main__":
    sys.exit(main())
