# SpiderFoot — Agent Operations Guide

**There is no SpiderFoot MCP.** The agent drives SpiderFoot via **terminal + optional web UI**, then reads output files in the workspace.

---

## What SpiderFoot does

Automated OSINT: given a **domain, email, IP, phone, or username**, SpiderFoot queries dozens of passive/active modules (DNS, WHOIS, breaches, social hints, etc.) and builds a relationship graph.

**Use after** Playwright harvest yields verified emails, domains, or usernames — not as a replacement for human-like browsing.

---

## Install (agent runs once per machine)

```bash
cd skills/person-osint-pipeline/scripts
./install_osint_tools.sh
```

Verify:

```bash
source scripts/resolve_paths.sh
test -f "$SPIDERFOOT_SF" && echo OK
```

---

## Two ways to run

### A — Module-targeted CLI scan (preferred for pipeline)

```bash
./run_spiderfoot.sh \
  --workspace /abs/path/{subject}_osint \
  --target "markknoffler" \
  --target-type USERNAME
```

Uses a **safe default module set** per target type (does not load all 200+ modules).

Override modules: `--modules sfp_github,sfp_accounts`

Output: `{workspace}/tools/spiderfoot/{scan_id}/results.json`

**Note:** `-u passive` loads every module and requires the full dependency tree. Use explicit `-m` via `run_spiderfoot.sh` instead.

### B — Web UI + sfcli (long scans)

Terminal 1 — start server (keep open):

```bash
cd "$SPIDERFOOT_HOME"
python3 sf.py -l 127.0.0.1:5001
```

Terminal 2 — agent or user opens `http://127.0.0.1:5001`, starts scan, exports JSON to workspace.

**Do not** run web server and Playwright MCP daemon on the same profile lock — use separate terminals.

---

## Agent workflow (per target)

1. **Gate:** Target must be `CANDIDATE` or `VERIFIED` in `identifiers_index.md` OR derived from a **VERIFIED** social account.
2. Log step: `log_step.py --step "SpiderFoot scan target=..."`.
3. Run `run_spiderfoot.sh` with `--use-case passive` first.
4. Read `results.json` → extract new emails, domains, usernames → append to `identifiers_index.md` as `CANDIDATE`.
5. For each new **social URL** with possible face: Playwright harvest → face verify before marking VERIFIED.
6. Re-run SpiderFoot on newly verified emails/domains (iteration loop).

---

## Failure handling

| Issue | Action |
|-------|--------|
| `sf.py not found` | Run `install_osint_tools.sh` |
| Scan empty | Try `-t HUMAN_NAME` vs `-t USERNAME`; broaden use-case to `investigate` |
| Module errors | Re-run with `-u passive` only; log in run log |
| Rate limits | Pause 5 min; do not stack parallel scans |
| No face for username hit | Mark username REJECTED; do not attribute to subject |

---

## Ethics

SpiderFoot may surface breach data and third-party OSINT. **Never** attribute an email/username to the subject without face verification or multiple independent corroborations documented in `final_report.md`.
