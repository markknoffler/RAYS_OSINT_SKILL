#!/usr/bin/env bash
# Print absolute paths for skill scripts — source or run from any directory.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="${OSINT_TOOLS_ROOT:-$HOME/.local/share/osint-tools}"
SPIDERFOOT_HOME="${SPIDERFOOT_HOME:-$TOOLS_ROOT/spiderfoot}"
echo "SKILL_DIR=$SCRIPT_DIR/.."
echo "SKILL_SCRIPTS=$SCRIPT_DIR"
echo "PYTHON=$SCRIPT_DIR/.venv/bin/python"
echo "VENV=$SCRIPT_DIR/.venv"
echo "OSINT_TOOLS_ROOT=$TOOLS_ROOT"
echo "SPIDERFOOT_HOME=$SPIDERFOOT_HOME"
echo "SPIDERFOOT_SF=$SPIDERFOOT_HOME/sf.py"
