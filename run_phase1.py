#!/usr/bin/env python3
"""
CLI entrypoint for Phase 1: Review Ingestion and Cleaning.
Run from project root: python run_phase1.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase1.run import main

if __name__ == "__main__":
    sys.exit(main())
