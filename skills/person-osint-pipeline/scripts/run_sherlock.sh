#!/usr/bin/env bash
# Run Sherlock username enumeration → workspace/tools/sherlock/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$(bash "$SCRIPT_DIR/resolve_paths.sh")"

WORKSPACE=""
USERNAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --username) USERNAME="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$WORKSPACE" || -z "$USERNAME" ]]; then
  echo "Usage: run_sherlock.sh --workspace PATH --username NAME"
  exit 1
fi

OUT_DIR="$WORKSPACE/tools/sherlock"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
TXT="$OUT_DIR/${USERNAME}_${STAMP}.txt"

SHERLOCK_BIN="$VENV/bin/sherlock"
if [[ ! -x "$SHERLOCK_BIN" ]]; then
  SHERLOCK_BIN="$(command -v sherlock || true)"
fi
if [[ -z "$SHERLOCK_BIN" ]]; then
  echo "Sherlock not installed. Run: ./install_osint_tools.sh"
  exit 1
fi

echo "Sherlock: $USERNAME"
"$SHERLOCK_BIN" "$USERNAME" --print-found --timeout 10 2>&1 | tee "$TXT"
echo "Saved: $TXT"
