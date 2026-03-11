#!/usr/bin/env python3
"""
CLI entrypoint for Phase 4: Email Delivery.
Run from project root: python run_phase4.py
Requires: Phase 3 output (data/weekly_notes/weekly_note.json).
Recipient: when called from front-end, pass run_phase4(recipient_email=..., recipient_name=...) for personalized "Hi, {name},". For CLI, set EMAIL_TO and optional recipient_name in config.
To send: set SMTP_* in .env, recipient (see above), and email_dry_run: false in config.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase4.run import main

if __name__ == "__main__":
    sys.exit(main())
