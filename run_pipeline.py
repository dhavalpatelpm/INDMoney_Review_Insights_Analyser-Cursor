#!/usr/bin/env python3
"""
CLI: Run the INDmoney Review Insights pipeline (Phases 1-4).
Usage:
  python run_pipeline.py              # Run Phase 1 → 2 → 3 → 4 (full pipeline)
  python run_pipeline.py --phase 1    # Phase 1 only (fetch & clean)
  python run_pipeline.py --phase 2    # Phase 2 only (themes)
  python run_pipeline.py --phase 3    # Phase 3 only (weekly note)
  python run_pipeline.py --phase 4    # Phase 4 only (email)
  python run_pipeline.py --phase 1,2,3   # Run phases 1, 2, 3 (generate one-pager)
  python run_pipeline.py --phase 4 --email x@y.com --name "John"  # Send email
"""
import argparse
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

from phase1.run import run_phase1
from phase2.run import run_phase2
from phase3.run import run_phase3
from phase4.run import run_phase4


def main() -> int:
    parser = argparse.ArgumentParser(description="INDmoney Review Insights Pipeline")
    parser.add_argument(
        "--phase",
        type=str,
        default="1,2,3,4",
        help="Phases to run: 1,2,3,4 or comma-separated (e.g. 1,2,3)",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Recipient email for Phase 4",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Recipient name for Phase 4 (personalized greeting)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Phase 4 only: save draft, do not send email",
    )
    args = parser.parse_args()

    phases = [p.strip() for p in args.phase.split(",") if p.strip()]

    for p in phases:
        if p not in ("1", "2", "3", "4"):
            print(f"Invalid phase: {p}. Use 1, 2, 3, or 4.", file=sys.stderr)
            return 1

    if "4" in phases and not args.dry_run and not args.email:
        print("Phase 4 requires --email when sending. Use --dry-run to preview only.", file=sys.stderr)
        return 1

    try:
        if "1" in phases:
            run_phase1()
        if "2" in phases:
            run_phase2()
        if "3" in phases:
            run_phase3()
        if "4" in phases:
            import yaml
            config_path = ROOT / "config" / "settings.yaml"
            cfg = {}
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
            cfg["email_dry_run"] = args.dry_run
            run_phase4(
                config=cfg,
                recipient_email=args.email,
                recipient_name=args.name,
            )
    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
