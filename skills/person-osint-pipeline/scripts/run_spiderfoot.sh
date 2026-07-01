#!/usr/bin/env bash
# Run SpiderFoot scan; write JSON to workspace/tools/spiderfoot/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$(bash "$SCRIPT_DIR/resolve_paths.sh")"

WORKSPACE=""
TARGET=""
TARGET_TYPE="USERNAME"
USE_CASE="passive"
MODULES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --target-type) TARGET_TYPE="$2"; shift 2 ;;
    --use-case) USE_CASE="$2"; shift 2 ;;
    --modules) MODULES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$WORKSPACE" || -z "$TARGET" ]]; then
  echo "Usage: run_spiderfoot.sh --workspace PATH --target VALUE [--target-type TYPE] [--use-case passive|investigate|footprint] [--modules mod1,mod2]"
  exit 1
fi

if [[ ! -f "$SPIDERFOOT_SF" ]]; then
  echo "SpiderFoot not installed. Run: ./install_osint_tools.sh"
  exit 1
fi

# Default module sets (avoid loading all modules — requires full dependency tree)
if [[ -z "$MODULES" ]]; then
  case "$TARGET_TYPE" in
    USERNAME) MODULES="sfp_github,sfp_accounts,sfp_socialprofiles,sfp_wikipediaedits" ;;
    EMAILADDR) MODULES="sfp_emailrep,sfp_hunter,sfp_gravatar,sfp_breachdirectory" ;;
    DOMAIN_NAME|INTERNET_NAME) MODULES="sfp_dnsresolve,sfp_whois,sfp_sslcert,sfp_subdomain" ;;
    HUMAN_NAME) MODULES="sfp_names,sfp_wikipediaedits,sfp_socialprofiles" ;;
    *) MODULES="sfp_dnsresolve,sfp_whois" ;;
  esac
fi

SLUG="$(python3 -c "import re; print(re.sub(r'[^a-zA-Z0-9._-]+','_', '''$TARGET''')[:80])")"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$WORKSPACE/tools/spiderfoot/${SLUG}_${STAMP}"
mkdir -p "$OUT_DIR"

# Timeout (seconds) — SpiderFoot can hang on slow modules
SF_TIMEOUT="${SPIDERFOOT_TIMEOUT:-180}"

echo "SpiderFoot: target=$TARGET type=$TARGET_TYPE modules=$MODULES (timeout ${SF_TIMEOUT}s)"
echo "Output: $OUT_DIR"

PY="$VENV/bin/python3"
cd "$SPIDERFOOT_HOME"

# Prefer explicit -m (reliable on Python 3.13); -u loads all modules
timeout "$SF_TIMEOUT" "$PY" sf.py \
  -s "$TARGET" \
  -t "$TARGET_TYPE" \
  -m "$MODULES" \
  -o json \
  -q \
  > "$OUT_DIR/results.json" 2>"$OUT_DIR/sf.stderr" || SF_EXIT=$?
SF_EXIT=${SF_EXIT:-0}

if [[ "$SF_EXIT" -eq 124 ]]; then
  echo "SpiderFoot timed out after ${SF_TIMEOUT}s — partial results may exist in spiderfoot DB; use web UI for long scans"
fi
if [[ "$SF_EXIT" -ne 0 && "$SF_EXIT" -ne 124 ]]; then
    echo "SpiderFoot exited non-zero; see $OUT_DIR/sf.stderr"
    tail -30 "$OUT_DIR/sf.stderr" 2>/dev/null || true
    exit 1
fi

BYTES=$(wc -c < "$OUT_DIR/results.json" | tr -d ' ')
echo "Wrote $OUT_DIR/results.json ($BYTES bytes)"
if [[ "$BYTES" -lt 10 ]]; then
  echo "WARNING: empty or tiny results — try --modules with fewer modules or start web UI (docs/SPIDERFOOT.md)"
  exit 2
fi
