# OSINT Tool Chain — Reference

Tools integrate **after** Playwright discovery and **before** final report. All tool outputs are **candidates** until cross-verified (see `CROSS_VERIFICATION.md`).

| Tool | Input | Install | Agent runs via | Output dir |
|------|-------|---------|----------------|------------|
| **SpiderFoot** | domain, email, IP, username | `install_osint_tools.sh` | `run_spiderfoot.sh` | `tools/spiderfoot/` |
| **Sherlock** | username | same | `run_sherlock.sh` | `tools/sherlock/` |
| **Holehe** | email | same | `run_holehe.sh` | `tools/holehe/` |
| **Epieos** | email | browser (no install) | Playwright MCP → epieos.com | `tools/epieos/` |
| **IntelTechniques** | email, phone, username | browser | Playwright MCP → inteltechniques.com | `tools/inteltechniques/` |
| **Overpass Turbo** | lat/lon query | browser | Playwright MCP → overpass-turbo.eu | `locations/overpass/` |
| **Google (plain)** | name | — | Playwright MCP | SERP harvest |
| **InsightFace** | images | `setup_venv.sh` | `verify_accounts.py` | account status |

**Not automated (document-only):** Hunchly (manual browser extension for evidence trail), PACER/court records (Playwright + manual export), GrayKey/Cellebrite (law enforcement only — out of scope).

---

## Install all CLI tools

```bash
cd skills/person-osint-pipeline/scripts
./install_osint_tools.sh
./setup_venv.sh   # InsightFace for face verify
```

---

## Recommended order (Mode A — known subject)

1. Phase 1 Playwright Google (Session A → B)
2. Phase 2 deep harvest + face verify
3. Extract usernames/emails → `identifiers_index.md`
4. Sherlock on **verified** usernames only
5. Holehe + Epieos on **verified** emails only
6. SpiderFoot on verified email / domain / username
7. Playwright harvest any new social URLs from tool output
8. Face verify again → filter → re-run tools on new verified seeds
9. Relationship / org mapping (Phase 10)
10. Location synthesis (Overpass + VLM)

---

## Recommended order (Mode B — hypothesis, no initial face)

See `HYPOTHESIS_DISCOVERY_MODE.md`.

---

## Run logging (mandatory)

Every tool invocation and MCP navigation:

```bash
python scripts/log_step.py \
  --workspace /path/to/workspace \
  --cwd /path/to/project \
  --phase "T3-sherlock" \
  --step "Run Sherlock on markknoffler" \
  --status ok \
  --notes "47 hits, 3 overlap with verified GitHub"
```

Also writes to `{cwd}/OSINT_RUN_LOG.md` when `--cwd` is set.
