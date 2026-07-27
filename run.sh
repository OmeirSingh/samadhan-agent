#!/usr/bin/env bash
# One-command launcher for Samadhan-Agent.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "→ Creating virtualenv & installing dependencies (first run only)…"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

echo "→ Starting Samadhan-Agent on http://127.0.0.1:8000"
echo "  (Set ANTHROPIC_API_KEY in backend/.env to enable the live LLM agent;"
echo "   otherwise it runs in rule-based fallback mode.)"
exec ./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
