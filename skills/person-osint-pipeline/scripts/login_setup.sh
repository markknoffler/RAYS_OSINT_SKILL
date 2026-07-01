#!/usr/bin/env bash
# One-time (or rare) login setup: keeps Firefox open 20 min for LinkedIn + Instagram.
# Sessions persist in ~/.cursor/playwright-osint-profile for all future MCP runs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="${PLAYWRIGHT_OSINT_PROFILE:-$HOME/.cursor/playwright-osint-profile}"
MINUTES="${LOGIN_MINUTES:-20}"

# Kill MCP server only (never kill keep_login_open from this script's parent)
pkill -f "@playwright/mcp@latest.*8931" 2>/dev/null || true
pkill -f "playwright-mcp.*8931" 2>/dev/null || true
sleep 1

mkdir -p "$PROFILE"

if [[ ! -d "$SCRIPT_DIR/node_modules/playwright" ]]; then
  echo "Installing playwright (first time only)..."
  cd "$SCRIPT_DIR" && npm install playwright --no-save
  npx playwright install firefox
fi

export PLAYWRIGHT_OSINT_PROFILE="$PROFILE"
export LOGIN_MINUTES="$MINUTES"

echo "Starting login browser (${MINUTES} min)..."
exec node "$SCRIPT_DIR/keep_login_open.mjs"
