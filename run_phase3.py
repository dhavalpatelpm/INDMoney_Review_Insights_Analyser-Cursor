#!/usr/bin/env python3
"""
CLI entrypoint for Phase 3: Weekly Note Generation (Gemini).
Run from project root: python run_phase3.py
Requires: GOOGLE_API_KEY or GEMINI_API_KEY in .env; Phase 2 output at data/themed_reviews.json.
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

from phase3.run import main

if __name__ == "__main__":
    sys.exit(main())
