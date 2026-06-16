#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Virtual environment ready: $SCRIPT_DIR/.venv"
echo "Run scripts with: $SCRIPT_DIR/.venv/bin/python verify_accounts.py --workspace /path/to/subject_osint"
