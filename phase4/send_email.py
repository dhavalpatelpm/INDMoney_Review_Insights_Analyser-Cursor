"""
Send email via SMTP. Credentials from environment.
Recipient: pass recipient_email (e.g. from front-end) or set EMAIL_TO in env for CLI.
"""
from __future__ import annotations

import os
import smtplib
from pathlib import Path
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any


def get_smtp_config() -> dict[str, Any]:
    """Read SMTP config from environment. Recipient (to) is optional; can be passed to send_email instead."""
    password = (os.environ.get("SMTP_PASSWORD") or os.environ.get("SMTP_APP_PASSWORD") or "").strip()
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": password,
        "to": os.environ.get("EMAIL_TO", "").strip(),
        "from_addr": (os.environ.get("EMAIL_FROM") or os.environ.get("SMTP_USER") or "").strip(),
    }


def send_email(
    subject: str,
    body: str,
    recipient_email: str | None = None,
    *,
    html: bool = True,
    logo_path: Path | None = None,
    logo_cid: str = "indmoney_logo",
) -> None:
    """
    Send email via SMTP. By default sends HTML body (bold title/headings, normal text).
    recipient_email: pass from front-end (or config); if None, falls back to EMAIL_TO in environment.
    logo_path: optional path to logo image; if provided and exists, attaches as inline (cid) for HTML display.
    Raises if SMTP credentials missing, or if no recipient when sending.
    """
    cfg = get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        raise RuntimeError("Set SMTP_USER and SMTP_PASSWORD (or SMTP_APP_PASSWORD for Gmail) in environment")

    to_addr = (recipient_email or "").strip() or cfg["to"]
    if not to_addr:
        raise RuntimeError("Provide recipient_email (e.g. from front-end) or set EMAIL_TO in environment")

    use_logo = logo_path and Path(logo_path).exists()
    msg = MIMEMultipart("related" if use_logo else "alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"] or cfg["user"]
    msg["To"] = to_addr
    subtype = "html" if html else "plain"
    msg.attach(MIMEText(body, subtype, "utf-8"))
    if use_logo:
        img_data = Path(logo_path).read_bytes()
        img = MIMEImage(img_data, _subtype="png")
        img.add_header("Content-ID", f"<{logo_cid}>")
        img.add_header("Content-Disposition", "inline", filename="indmoney_logo.png")
        msg.attach(img)

    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(msg["From"], [to_addr], msg.as_string())
