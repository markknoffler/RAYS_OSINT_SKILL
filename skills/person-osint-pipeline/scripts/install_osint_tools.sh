#!/usr/bin/env bash
# Install SpiderFoot, Sherlock, Holehe for the OSINT pipeline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="${OSINT_TOOLS_ROOT:-$HOME/.local/share/osint-tools}"
SPIDERFOOT_DIR="$TOOLS_ROOT/spiderfoot"
VENV="$SCRIPT_DIR/.venv"

mkdir -p "$TOOLS_ROOT"

echo "==> OSINT tools root: $TOOLS_ROOT"

# Python venv for pipeline + holehe/sherlock
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"
pip install -q -r "$SCRIPT_DIR/spiderfoot-requirements.txt"
pip install -q holehe sherlock-project 2>/dev/null || pip install -q holehe "sherlock-project[project]"

# SpiderFoot — clone if missing
if [[ ! -f "$SPIDERFOOT_DIR/sf.py" ]]; then
  echo "==> Cloning SpiderFoot..."
  git clone --depth 1 https://github.com/smicallef/spiderfoot.git "$SPIDERFOOT_DIR"
else
  echo "==> SpiderFoot already present: $SPIDERFOOT_DIR"
fi

# Write env snippet
ENV_FILE="$SCRIPT_DIR/osint_tools.env"
cat > "$ENV_FILE" <<EOF
# Source after install: eval "\$(bash $SCRIPT_DIR/resolve_paths.sh)"
export OSINT_TOOLS_ROOT="$TOOLS_ROOT"
export SPIDERFOOT_HOME="$SPIDERFOOT_DIR"
export SPIDERFOOT_SF="$SPIDERFOOT_DIR/sf.py"
EOF

echo ""
echo "Installed:"
echo "  SpiderFoot: $SPIDERFOOT_DIR/sf.py"
echo "  Sherlock:   $(command -v sherlock || echo '$VENV/bin/sherlock')"
echo "  Holehe:     $(command -v holehe || echo '$VENV/bin/holehe')"
echo ""
echo "Run: eval \"\$(bash $SCRIPT_DIR/resolve_paths.sh)\""
