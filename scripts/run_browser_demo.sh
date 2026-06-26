#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${OFFEROPS_VENV_DIR:-.venv}"
PYTHON_BIN="$VENV_DIR/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  python3 -m venv "$VENV_DIR"
fi

env PYTHONPATH=src "$PYTHON_BIN" scripts/browser_demo_router.py "$@"
