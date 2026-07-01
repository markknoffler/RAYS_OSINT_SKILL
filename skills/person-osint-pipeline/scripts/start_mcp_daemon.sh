#!/usr/bin/env bash
# Long-running Playwright MCP server. KEEP THIS TERMINAL OPEN while investigating.
# Cursor should use url: http://localhost:8931/mcp (see .cursor/mcp.json)
set -euo pipefail

PROFILE="${PLAYWRIGHT_OSINT_PROFILE:-$HOME/.cursor/playwright-osint-profile}"
PORT="${PLAYWRIGHT_MCP_PORT:-8931}"

mkdir -p "$PROFILE"

# Don't run if login browser script is using the same profile
if pgrep -f "keep_login_open.mjs" >/dev/null 2>&1; then
  echo "ERROR: login_setup.sh is still running. Finish login first, then start MCP."
  exit 1
fi

pkill -f "playwright-mcp.*${PORT}" 2>/dev/null || true
sleep 1

echo ""
echo "Playwright MCP daemon — port ${PORT}"
echo "Profile: ${PROFILE}"
echo "Keep this terminal open. Ctrl+C to stop."
echo ""

exec npx -y @playwright/mcp@latest \
  --browser=firefox \
  --user-data-dir "$PROFILE" \
  --allow-unrestricted-file-access \
  --shared-browser-context \
  --port "$PORT"
