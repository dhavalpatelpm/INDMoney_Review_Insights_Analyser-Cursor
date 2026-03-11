#!/usr/bin/env python3
"""
CLI entrypoint for Phase 2: Theme Discovery and Classification (Groq).
Uses filtered reviews from Phase 1 (data/cleaned_reviews.json). Loads GROQ_API_KEY from .env.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Load .env so GROQ_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.run import main

if __name__ == "__main__":
    sys.exit(main())
