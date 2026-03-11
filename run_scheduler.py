#!/usr/bin/env python3
"""
Scheduler: runs the pipeline every 5 minutes (e.g. 15:40, 15:45, 15:50 IST).
Recipient: dhavalpatel.sdds@gmail.com
Uses run_pipeline.py CLI: Phases 1-4 (fetch, themes, note, email).
Logs to logs/scheduler.log
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "scheduler.log"

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

SCHEDULED_RECIPIENT = "dhavalpatel.sdds@gmail.com"
SCHEDULED_RECIPIENT_NAME = "Dhaval Patel"

# Configure logging to file and console
LOG_DIR.mkdir(exist_ok=True)
_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# File handler
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.INFO)
_fh.setFormatter(_formatter)
logger.addHandler(_fh)
# Console handler
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_formatter)
logger.addHandler(_ch)


def run_weekly_pulse() -> None:
    """Invoke run_pipeline.py with Phases 1-4 and fixed recipient."""
    cmd = [
        sys.executable,
        str(ROOT / "run_pipeline.py"),
        "--phase", "1,2,3,4",
        "--email", SCHEDULED_RECIPIENT,
        "--name", SCHEDULED_RECIPIENT_NAME,
    ]
    logger.info("Scheduler: Running pipeline -> %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.info("pipeline: %s", line)
        if result.returncode != 0:
            logger.error("Scheduler: Pipeline exited with code %s", result.returncode)
            if result.stderr:
                for line in result.stderr.strip().splitlines():
                    logger.error("pipeline stderr: %s", line)
        else:
            logger.info("Scheduler: Pipeline completed successfully")
    except subprocess.TimeoutExpired:
        logger.error("Scheduler: Pipeline timed out after 10 minutes")
    except Exception as e:
        logger.exception("Scheduler: Pipeline failed: %s", e)


def main() -> int:
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("Install APScheduler: pip install APScheduler")
        return 1

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        run_weekly_pulse,
        CronTrigger(minute="*/5"),
        id="weekly_pulse",
    )
    logger.info(
        "Scheduler started. Pipeline every 5 min (15:40, 15:45, 15:50, ...) IST -> %s | Logs: %s",
        SCHEDULED_RECIPIENT, LOG_FILE,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
