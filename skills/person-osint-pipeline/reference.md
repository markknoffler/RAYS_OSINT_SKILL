# Person OSINT Pipeline — Reference

## File naming

| Artifact | Rule |
|----------|------|
| Workspace folder | `{subject_slug}_osint` in user CWD |
| Account directory | Social handle + platform suffix (`janedoe_ig`) |
| Profile screenshot | Always `profile.png` |
| Post screenshots | `{url_slug}.png` from post/media URL |
| `accounts_index.md` | Master table + optional image link log |

### Handle extraction examples

| URL | handle_dir |
|-----|------------|
| `https://instagram.com/janedoe` | `janedoe_ig` |
| `https://linkedin.com/in/jane-doe` | `jane-doe_linkedin` |
| `https://x.com/janedoe` | `janedoe_x` |
| `https://facebook.com/janedoe` | `janedoe_fb` |

Python helper: `scripts/utils/image_naming.py` → `extract_handle_from_url()`, `url_to_image_filename()`.

---

## Face verification thresholds

InsightFace `buffalo_l` cosine similarity (default **0.45**):

| Range | Interpretation |
|-------|----------------|
| ≥ 0.55 | Strong match |
| 0.45 – 0.55 | Likely same person — verify manually if borderline |
| < 0.45 | Reject account (Pass 1) or move to `related/` (Pass 2) |

Tune with `--threshold` / `--match-threshold` flags.

First run downloads models to `~/.insightface/models/` (one-time, offline thereafter).

---

## Playwright MCP setup

### Cursor

Repo includes `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

Install browsers once:

```bash
npx playwright install chromium
```

### Logged-in sessions (Instagram / LinkedIn)

Follower/following lists often require authentication. Options:

1. **Headed browser** — run Playwright MCP without `--headless`; log in manually when browser opens
2. **User data dir** — persist session:
   ```json
   "args": ["-y", "@playwright/mcp@latest", "--user-data-dir", "/path/to/playwright-profile"]
   ```
3. **Skip Phase 6** — document in `final_report.md` that network expansion was not possible

### Screenshot tips

- Wait for network idle after navigation
- Scroll incrementally to load lazy media
- Save screenshots to absolute paths under `{workspace}/accounts/{handle}/`
- Copy exact post URL from address bar or share link into `accounts_index.md`

---

## Platform limitations

| Platform | Public access | Followers/following | Bot risk |
|----------|---------------|---------------------|----------|
| Instagram | Partial | Usually login-required | High |
| LinkedIn | Limited | N/A | Very high |
| X / Twitter | Moderate | Partially public | Medium |
| Facebook | Very limited | Login-required | High |

**Recommendations:**
- Add 2–5 second delays between profile loads
- Cap network expansion at 50–100 users unless user explicitly extends scope
- Prefer public profile fields over aggressive scraping

---

## Script reference

All scripts run from `skills/person-osint-pipeline/scripts/` with venv Python.

### verify_accounts.py (Pass 1)

```bash
.venv/bin/python verify_accounts.py \
  --workspace /path/to/subject_osint \
  --reference reference.jpg \
  --threshold 0.45
```

### prune_faces.py (Pass 2)

```bash
.venv/bin/python prune_faces.py \
  --workspace /path/to/subject_osint \
  --reference reference.jpg \
  --match-threshold 0.45
```

### build_social_graph.py

```bash
.venv/bin/python build_social_graph.py \
  --workspace /path/to/subject_osint
```

Expects agent-populated `network/social_graph.csv` first.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No face detected in reference` | Use a clear frontal reference photo |
| InsightFace install fails on Apple Silicon | `pip install onnxruntime` (CPU build is fine) |
| Playwright MCP not found | Cursor Settings → MCP → reload; run `npx playwright install` |
| All accounts REJECTED | Lower threshold slightly (e.g. 0.40) or recheck reference photo |
| Empty social graph | Instagram login required; complete Phase 6 manually or skip |

---

## Legal & ethics

This pipeline collects **publicly available** information. Operators must:

- Obtain appropriate authorization before investigating third parties
- Comply with local privacy laws (GDPR, CCPA, etc.)
- Not use outputs for harassment, stalking, or discrimination
- Respect platform Terms of Service

The Phase 0 authorization gate in `SKILL.md` is mandatory.
