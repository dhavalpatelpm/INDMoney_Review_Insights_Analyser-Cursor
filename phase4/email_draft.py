"""
Build email subject and body from the weekly note.
Format: INDMoney logo at top, Hi {name}, bold title, headings, Best Regards Team INDMoney.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

SUBJECT_PREFIX = "INDmoney Weekly Pulse"
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "indmoney_logo.png"
LOGO_CID = "indmoney_logo"


MAX_QUOTE_LEN = 200
MAX_ACTION_LEN = 250


def _escape_html(s: str) -> str:
    """Escape HTML special characters."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate text to max_len, appending suffix when truncated."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)].rstrip() + suffix


def _logo_img_html() -> str:
    """Return HTML img tag for INDMoney logo (cid) if file exists. Use small size for email."""
    if not LOGO_PATH.exists():
        return ""
    return (
        f'<p style="margin: 0 0 1em 0;">'
        f'<img src="cid:{LOGO_CID}" alt="INDmoney" '
        f'style="width: 200px; height: auto; display: block;" /></p>'
    )


def build_draft(note: dict[str, Any], recipient_name: str | None = None) -> tuple[str, str]:
    """
    Build creative, visually engaging HTML email with doodles and personality.
    Returns (subject, body_html).
    """
    meta = note.get("meta") or {}
    date_range = meta.get("date_range", "")
    subject = f"{SUBJECT_PREFIX} — {date_range}" if date_range else SUBJECT_PREFIX

    now = datetime.now()
    week_of = now.strftime("%B %d, %Y")

    name = (recipient_name or "").strip()
    themes = note.get("themes", [])
    quotes = note.get("quotes", [])

    # Creative HTML email with inline styles (email-client safe)
    logo = _logo_img_html()
    greeting = f"Hi {_escape_html(name)},<br><br>" if name else ""
    intro = (
        "Here&apos;s your <strong>Weekly Review Pulse</strong> — a curated snapshot of what users "
        "are saying and where to focus next. ✨"
    )

    # Creative doodle-style dividers
    doodle_div = '<p style="margin: 16px 0; font-size: 20px; color: #6366f1; letter-spacing: 5px;">∼ ∿ ∽ ∼ ∿ ∽ ∼ ∿ ∽</p>'
    doodle_star = '<p style="margin: 12px 0; font-size: 14px; color: #00d4aa; letter-spacing: 3px;">✦ ─ ─ ─ ─ ─ ✦</p>'

    # Theme cards
    theme_html = []
    icons = ["📊", "💬", "🎯"]
    for i, theme in enumerate(themes, 1):
        icon = icons[(i - 1) % len(icons)]
        q = next((x for x in quotes if x.get("theme") == theme), None)
        qt = _truncate(q["text"], MAX_QUOTE_LEN) if q and q.get("text") else ""
        theme_html.append(
            f'<table cellpadding="12" cellspacing="0" border="0" width="100%" '
            f'style="margin-bottom: 16px; border-left: 4px solid #00d4aa; background: #f8fafc; border-radius: 8px;">'
            f'<tr><td style="font-family: sans-serif;">'
            f'<strong style="color: #0f172a;">{icon} {i}. {_escape_html(theme)}</strong>'
            f'</td></tr>'
        )
        if qt:
            theme_html.append(
                f'<tr><td style="font-family: sans-serif; color: #475569; font-style: italic; padding-top: 0;">'
                f'&ldquo;{_escape_html(qt)}&rdquo;'
                f'</td></tr>'
            )
        theme_html.append("</table>")

    # Actions section with creative styling
    actions = note.get("actions", [])
    action_items = "".join(
        f'<tr><td style="padding: 8px 0; color: #334155; font-family: sans-serif;">'
        f'<span style="color: #00d4aa; font-weight: bold;">✦</span> {_escape_html(_truncate(a, MAX_ACTION_LEN))}'
        f'</td></tr>' for a in actions
    )
    total = meta.get("total_reviews", 0)

    body_html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, sans-serif; color: #1e293b; line-height: 1.6;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="max-width: 600px; margin: 0 auto;">
{logo}
<p style="font-size: 16px; color: #334155;">{greeting}{intro}</p>
{doodle_div}
<p style="font-size: 20px; font-weight: bold; color: #0f172a; margin: 16px 0 8px 0;">
  INDmoney Weekly Review Pulse
</p>
<p style="font-size: 14px; color: #64748b; margin: 0 0 20px 0;">Week of {week_of}</p>
{doodle_div}

{doodle_star}
<p style="font-size: 14px; font-weight: bold; color: #6366f1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
  ☆ Key Themes from the Community ☆
</p>
{"".join(theme_html)}

{doodle_star}
<p style="font-size: 14px; font-weight: bold; color: #6366f1; text-transform: uppercase; letter-spacing: 1px; margin: 24px 0 12px 0;">
  ✦ Recommended Actions ✦
</p>
<table cellpadding="16" cellspacing="0" border="0" width="100%" style="background: #f1f5f9; border-radius: 8px;">
{action_items}
</table>

<p style="margin-top: 24px; font-size: 12px; color: #94a3b8;">
  📈 {total} reviews analyzed  ·  Period: {_escape_html(date_range)}
</p>
{doodle_div}

<p style="font-size: 15px; color: #334155; margin: 24px 0 8px 0;">
  Best Regards,<br>
  <strong style="color: #0f172a;">Team INDmoney</strong>
</p>
<p style="font-size: 11px; color: #94a3b8; margin-top: 16px;">
  Invest in Indian & US Markets from one app.
</p>
<p style="font-size: 26px; color: #6366f1; font-style: italic; margin-top: 12px; letter-spacing: 0.5px;">
  Crafted by Dhaval Patel for the Smart Investing
</p>
<p style="margin: 16px 0; font-size: 16px; color: #cbd5e1; letter-spacing: 6px;">· · · ✦ · · ·</p>
</td></tr>
</table>
</body>
</html>"""
    return subject, body_html.strip()


def build_draft_plain(note: dict[str, Any], recipient_name: str | None = None) -> tuple[str, str]:
    """Build plain-text body (for dry-run file or fallback)."""
    meta = note.get("meta") or {}
    date_range = meta.get("date_range", "")
    subject = f"{SUBJECT_PREFIX} — {date_range}" if date_range else SUBJECT_PREFIX
    lines = []
    name = (recipient_name or "").strip()
    if name:
        lines.append(f"Hi {name},")
        lines.append("")
    now = datetime.now()
    week_of = now.strftime("%B %d, %Y")
    lines.append(f"INDMoney Weekly Review Pulse -- Week of {week_of}")
    lines.append("")
    themes = note.get("themes", [])
    quotes = note.get("quotes", [])
    lines.append("Key Themes")
    for i, theme in enumerate(themes, 1):
        lines.append(f"{i}. {theme}")
        q = next((x for x in quotes if x.get("theme") == theme), None)
        if q and q.get("text"):
            qt = _truncate(q["text"], MAX_QUOTE_LEN)
            lines.append(f'Quote: "{qt}"')
        lines.append("")
    lines.append("Recommended Actions")
    for i, action in enumerate(note.get("actions", []), 1):
        at = _truncate(action, MAX_ACTION_LEN)
        lines.append(f"{i}. {at}")
    total = meta.get("total_reviews", 0)
    lines.append(f"Review count: {total}  |  Period: {date_range}")
    lines.append("")
    lines.append("Best Regards,")
    lines.append("Team INDMoney")
    return subject, "\n".join(lines)


def build_draft_from_text(note_text: str, date_range: str = "") -> tuple[str, str]:
    """Build subject and body when input is the raw note text (e.g. from .txt file)."""
    subject = f"{SUBJECT_PREFIX} — {date_range}" if date_range else SUBJECT_PREFIX
    return subject, note_text.strip()
