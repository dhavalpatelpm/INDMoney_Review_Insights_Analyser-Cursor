# Phase 10: CLI & WebUI

Phase 10 provides a unified CLI and a Next.js WebUI for the INDmoney Review Insights pipeline.

## Quick start

```bash
# CLI: generate one-pager
python run_pipeline.py --phase 1,2,3

# CLI: send email
python run_pipeline.py --phase 4 --email you@example.com --name "Your Name"
```

## CLI

Run the pipeline from the terminal:

```bash
# Full pipeline (Phase 1 → 2 → 3 → 4) - requires --email for Phase 4
python run_pipeline.py --phase 1,2,3,4 --email you@example.com --name "Your Name"

# Generate one-pager only (Phase 1, 2, 3)
python run_pipeline.py --phase 1,2,3

# Send email only (Phase 4) - uses latest note
python run_pipeline.py --phase 4 --email you@example.com --name "Your Name"

# Phase 4 dry run (save draft, don't send)
python run_pipeline.py --phase 4 --dry-run

# Run single phase
python run_pipeline.py --phase 1
python run_pipeline.py --phase 2
python run_pipeline.py --phase 3
```

## WebUI (Next.js)

### 1. Install dependencies

```bash
cd web
npm install
```

### 2. Start the API backend

```bash
# From project root
python -m api.main
# Or: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Next.js dev server

```bash
cd web
npm run dev
```

Open http://localhost:3000

### 4. Configure API URL (optional)

If the API runs on a different host/port, create `web/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Troubleshooting

- **Blank or "Connection refused" at http://localhost:3000**  
  - Ensure only one `npm run dev` is running. If something else uses port 3000, stop it or run `npm run dev` and use the port Next prints (e.g. http://localhost:3001).
- **"EMFILE: too many open files" in terminal**  
  - Your system limit for open files is low. Close other apps, or run: `ulimit -n 10240` (macOS/Linux) then start `npm run dev` again.
- **UI loads but buttons fail**  
  - Start the API in another terminal: `python3 -m api.main` (must be running on http://localhost:8000).

## WebUI Features

- **Generate One-Pager**: Runs Phases 1–3 (fetch reviews, themes, weekly note). Displays themes, quotes, and action ideas.
- **Load Latest Note**: Loads the last saved weekly note without re-running the pipeline.
- **Send Email**: Enter recipient email and name; optionally enable dry run to save draft without sending.

## Scheduler

The scheduler runs the full pipeline **every 5 minutes** (e.g. 15:40, 15:45, 15:50 IST) and emails the weekly note to **dhavalpatel.sdds@gmail.com**.

```bash
# Install dependency
pip install APScheduler

# Run scheduler (keeps running until stopped)
python run_scheduler.py
```

The scheduler uses `run_pipeline.py --phase 1,2,3,4 --email dhavalpatel.sdds@gmail.com --name "Dhaval Patel"`.

**Requirements:** `.env` must have `SMTP_*` and API keys (`GROQ_API_KEY`, `GOOGLE_API_KEY` or `GEMINI_API_KEY`). Ensure `config/settings.yaml` has `email_dry_run: false` for the scheduler to send emails.

**Logs:** Scheduler output is written to `logs/scheduler.log`.
