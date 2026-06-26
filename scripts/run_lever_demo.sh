#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEFAULT_URL="https://jobs.lever.co/field-ai/9c2b7b13-12d0-4c1a-a672-8c869228ec9d/apply?utm_source=Simplify&ref=Simplify"
URL="${1:-$DEFAULT_URL}"
if [[ $# -gt 0 ]]; then
  shift
fi

VENV_DIR="${OFFEROPS_VENV_DIR:-.venv}"
PYTHON_BIN="$VENV_DIR/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  python3 -m venv "$VENV_DIR"
fi

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import playwright
PY
then
  "$PYTHON_BIN" -m pip install -r requirements-dev.txt
fi

mkdir -p artifacts

env PYTHONPATH=src "$PYTHON_BIN" scripts/lever_browser_fill_demo.py "$URL" \
  --profile-file "${OFFEROPS_PROFILE_FILE:-tests/fixtures/browser_applicant_profile.json}" \
  --user-data-dir "${OFFEROPS_BROWSER_PROFILE:-/tmp/offerops-lever-playwright-mvp}" \
  --screenshot "${OFFEROPS_SCREENSHOT:-artifacts/lever_fill_demo.png}" \
  --timeout "${OFFEROPS_TIMEOUT:-30}" \
  "$@"
