# RAYSpy-OSINT

Person OSINT investigation **skill pack** for Cursor, Claude Code, Codex, and other VLM-capable agents. Orchestrates Playwright MCP browser automation, local InsightFace face verification, and structured markdown artifacts in the user's working directory.

This repo is **separate** from the [RAYSpy](../RAYSpy/) 3D globe application.

---

## What it does

Given a **subject name** and **reference photo**, the agent:

1. Discovers social media profiles (Instagram, LinkedIn, X, Facebook)
2. Screenshots profile and post media (Playwright MCP)
3. Verifies identity with **local face recognition** (no paid API)
4. Prunes non-subject faces into `related/`
5. Scrapes profile metadata into per-account markdown files
6. Expands Instagram follower/following network (when accessible)
7. Infers locations using VLM prompts + network context
8. Produces `final_report.md`

See [skills/person-osint-pipeline/SKILL.md](skills/person-osint-pipeline/SKILL.md) for the full phased workflow.

---

## Prerequisites

| Requirement | Version / notes |
|-------------|-----------------|
| Node.js | 18+ |
| Python | 3.10+ |
| Playwright browsers | `npx @playwright/mcp install-browser chrome-for-testing` |
| VLM agent | Claude, Codex, Hermes, or Cursor with vision |
| Authorization | Legitimate purpose required — see skill Phase 0 |

---

## Quick start

### 1. Install the skill

Copy or symlink into your agent skills directory:

```bash
# Cursor personal skills
ln -s "$(pwd)/skills/person-osint-pipeline" ~/.cursor/skills/person-osint-pipeline

# Or Claude Code
ln -s "$(pwd)/skills/person-osint-pipeline" ~/.claude/skills/person-osint-pipeline
```

### 2. Python face-verification scripts

```bash
cd skills/person-osint-pipeline/scripts
./setup_venv.sh
```

First run downloads InsightFace `buffalo_l` models (~100MB) to `~/.insightface/models/`.

### 3. Playwright MCP (Cursor / Codex)

This repo includes [`.cursor/mcp.json`](.cursor/mcp.json). In Cursor or Codex:

1. Open this project folder (or copy `mcp.json` to `~/.codex/mcp.json`)
2. **Settings → MCP** → enable `playwright`
3. Run once:

```bash
npx @playwright/mcp install-browser chrome-for-testing
```

MCP config uses **headed Chrome** (no `--headless`), `--user-data-dir` for persistent Instagram/LinkedIn login, and `--allow-unrestricted-file-access` so screenshots save to `{workspace}/accounts/`. Log in once in the visible browser window; the agent pauses for you on CAPTCHAs.

### 4. Run an investigation

From the directory where you want artifacts created:

```
Using person-osint-pipeline, investigate Jane Doe.
Reference photo: /path/to/jane_reference.jpg
Authorized by: [your org / self]
Purpose: [legitimate purpose]
```

The agent creates `./jane_doe_osint/` with all artifacts.

---

## Repository layout

```
RAYSpy-OSINT/
├── README.md
├── .cursor/mcp.json
├── skills/person-osint-pipeline/
│   ├── SKILL.md              # Main agent orchestration
│   ├── reference.md          # Platform limits, troubleshooting
│   ├── templates/            # MD templates for artifacts
│   └── scripts/
│       ├── setup_venv.sh
│       ├── verify_accounts.py
│       ├── prune_faces.py
│       ├── build_social_graph.py
│       └── utils/
└── examples/sample_workspace/
```

---

## Scripts (local, free, offline)

| Script | Purpose |
|--------|---------|
| `verify_accounts.py` | Pass 1 — delete accounts with no face match |
| `prune_faces.py` | Pass 2 — move non-subject faces to `related/` |
| `build_social_graph.py` | Dedupe `network/social_graph.csv` |

```bash
SCRIPTS=skills/person-osint-pipeline/scripts
$SCRIPTS/.venv/bin/python $SCRIPTS/verify_accounts.py \
  --workspace ./jane_doe_osint --reference reference.jpg
```

**Identity matching is script-only** — the VLM is not used for face similarity scores.

---

## Ethics & legal

- Only investigate individuals when you have **appropriate authorization**
- Do not use for harassment, stalking, or non-consensual surveillance
- Respect platform Terms of Service and rate limits
- Investigation workspaces (`*_osint/`) are gitignored — never commit subject data

---

## Related project

**[RAYSpy](../RAYSpy/)** — open-data 3D globe (satellites, flights, CCTV, earthquakes). Optional future integration with location outputs from this pipeline.

---

## License

Private research tooling. Third-party dependencies (InsightFace, Playwright, etc.) are subject to their own licenses. Public data sources are governed by their respective terms.
