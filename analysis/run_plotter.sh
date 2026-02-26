#!/usr/bin/env bash
# Run the plotter with its dependencies in a project venv (avoids system pip).
# Usage: from repo root, ./analysis/run_plotter.sh [path] [-o out_dir] [--no-show]

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO_ROOT/.venv"
ACTIVATE="$VENV/bin/activate"

if [[ ! -f "$ACTIVATE" ]]; then
  echo "Creating venv at $VENV ..."
  python3 -m venv "$VENV" || {
    echo "Failed to create venv. Install python3-venv: sudo apt install python3-venv python3-full"
    exit 1
  }
  [[ -f "$ACTIVATE" ]] || { echo "Venv missing $ACTIVATE"; exit 1; }
fi
source "$ACTIVATE"
pip install -q -r "$REPO_ROOT/analysis/requirements.txt"
exec python3 "$REPO_ROOT/analysis/plotter.py" "$@"
