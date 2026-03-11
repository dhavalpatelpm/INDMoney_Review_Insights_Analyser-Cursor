"""
FastAPI backend for INDmoney Review Insights.
Endpoints: run pipeline (1-3), load note, send email (Phase 4).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from phase1.run import run_phase1
from phase2.run import run_phase2
from phase3.run import run_phase3
from phase4.run import run_phase4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="INDmoney Review Insights API",
    description="Generate weekly review pulse and send email",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SendEmailRequest(BaseModel):
    recipient_email: str
    recipient_name: Optional[str] = None
    dry_run: bool = False


class PipelineResponse(BaseModel):
    success: bool
    message: str
    note: Optional[dict] = None


class SendEmailResponse(BaseModel):
    success: bool
    message: str


def _load_config() -> dict:
    import yaml
    path = ROOT / "config" / "settings.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_latest_note() -> Optional[dict]:
    cfg = _load_config()
    data_dir = ROOT / cfg.get("data_dir", "data")
    notes_dir = cfg.get("weekly_notes_dir", "weekly_notes")
    note_filename = cfg.get("weekly_note_filename", "weekly_note")
    path = data_dir / notes_dir / f"{note_filename}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def root():
    return {"status": "ok", "service": "INDmoney Review Insights API"}


@app.get("/api/note", response_model=PipelineResponse)
def get_note():
    """Load the latest weekly note (from Phase 3 output)."""
    note = _load_latest_note()
    if not note:
        return PipelineResponse(
            success=False,
            message="No weekly note found. Run the pipeline (Phases 1-3) first.",
            note=None,
        )
    return PipelineResponse(success=True, message="Note loaded", note=note)


@app.post("/api/pipeline", response_model=PipelineResponse)
def run_pipeline():
    """
    Run Phases 1, 2, 3 to generate the weekly one-pager.
    Returns the generated note.
    """
    try:
        run_phase1()
        run_phase2()
        note = run_phase3()
        return PipelineResponse(
            success=True,
            message="Pipeline completed. Weekly note generated.",
            note=note,
        )
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-email", response_model=SendEmailResponse)
def send_email(req: SendEmailRequest):
    """
    Run Phase 4: send the weekly note email to the recipient.
    Recipient email and name are required (name for "Hi, {name}," greeting).
    """
    try:
        cfg = _load_config()
        cfg["email_dry_run"] = req.dry_run
        subject, _ = run_phase4(
            config=cfg,
            recipient_email=req.recipient_email.strip(),
            recipient_name=(req.recipient_name or "").strip() or None,
        )
        if req.dry_run:
            return SendEmailResponse(success=True, message="Dry run: draft saved, not sent.")
        return SendEmailResponse(success=True, message=f"Email sent to {req.recipient_email}")
    except Exception as e:
        logger.exception("Send email failed")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
