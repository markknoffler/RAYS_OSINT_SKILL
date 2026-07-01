#!/usr/bin/env bash
# Run Holehe email registration check → workspace/tools/holehe/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$(bash "$SCRIPT_DIR/resolve_paths.sh")"

WORKSPACE=""
EMAIL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$WORKSPACE" || -z "$EMAIL" ]]; then
  echo "Usage: run_holehe.sh --workspace PATH --email ADDRESS"
  exit 1
fi

OUT_DIR="$WORKSPACE/tools/holehe"
mkdir -p "$OUT_DIR"
SLUG="$(echo "$EMAIL" | tr '@' '_at_' | tr -cd '[:alnum:]_-.')"
STAMP="$(date +%Y%m%d_%H%M%S)"
TXT="$OUT_DIR/${SLUG}_${STAMP}.txt"

HOLEHE_BIN="$VENV/bin/holehe"
if [[ ! -x "$HOLEHE_BIN" ]]; then
  HOLEHE_BIN="$(command -v holehe || true)"
fi
if [[ ! -x "$HOLEHE_BIN" ]]; then
  echo "Holehe not installed. Run: ./install_osint_tools.sh"
  exit 1
fi

echo "Holehe: $EMAIL"
"$HOLEHE_BIN" "$EMAIL" 2>&1 | tee "$TXT"
echo "Saved: $TXT"
