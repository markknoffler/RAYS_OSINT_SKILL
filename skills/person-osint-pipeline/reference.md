# Person OSINT Pipeline — Reference

## Persistent browser sessions (read first)

The user logs into LinkedIn and Instagram **once**. All future agent sessions reuse the same cookies.

### Required MCP config

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp@latest",
        "--browser=firefox",
        "--user-data-dir",
        "/home/mark/.cursor/playwright-osint-profile",
        "--allow-unrestricted-file-access"
      ]
    }
  }
}
```

**Use the same `--user-data-dir` path every time.** Never change it between sessions or logins will be lost.

| Do | Do not |
|----|--------|
| Fixed `--user-data-dir` path | Omit `--user-data-dir` (temp profile, lost on close) |
| Headed browser (no `--headless`) | `--headless` (blocked by LinkedIn/Instagram) |
| `--allow-unrestricted-file-access` | Restricted file access (screenshots fail) |
| `--browser=firefox` | User's Firefox via Playwright |
| `--browser=chromium` | Fallback on Arch if Firefox fails |

Install browser once:

```bash
npx @playwright/mcp install-browser chrome-for-testing
```

### Session persistence checklist

- [ ] `mcp.json` has fixed `--user-data-dir`
- [ ] No `--isolated` flag present
- [ ] User logged in once in the MCP browser window
- [ ] Agent verified feed/home visible (not login form) before investigations

Profile data lives at: `~/.cursor/playwright-osint-profile/`

---

## Agent vs scripts

| Task | Who |
|------|-----|
| Google search, open links, screenshots, scrolling, metadata scrape | **Agent** via MCP tools |
| Face identity matching, delete/reject accounts, move related faces | **Python scripts** |
| Face-visible gate (is there a face in this screenshot?) | **Agent VLM** |
| Face identity score (is this the subject?) | **`verify_accounts.py` only** |

**Deprecated — do not use for investigations:**
- `scripts/run_osint_mcp.mjs`
- `scripts/run_full_osint.mjs`
- `scripts/test_mcp_discovery.mjs`

These were dev harnesses. The agent must call MCP tools directly per `SKILL.md`.

---

## MCP tool cheat sheet

| Phase | Tool | Purpose |
|-------|------|---------|
| Discovery | `browser_navigate` | Google, profiles, articles |
| Discovery | `browser_snapshot` | Read page; get `ref=eN` for clicks |
| Discovery | `browser_click` | Search-by-image, pagination, load-more |
| Discovery | `browser_file_upload` | Reverse image search |
| Harvest | `browser_take_screenshot` | `profile.png`, post images |
| Harvest | `browser_press_key` | Scroll: `PageDown`, `End`, `PageUp` (no `browser_scroll`) |
| Harvest | `browser_mouse_wheel` | Pixel scroll (requires `--caps=vision`) |
| Metadata | `browser_snapshot` | Bio, posts, captions |

Screenshot filenames must be **absolute**:

```
{workspace}/accounts/{handle_dir}/profile.png
{workspace}/accounts/{handle_dir}/{url_slug}.png
{workspace}/articles/{slug}.md
```

See `MCP_TOOL_MAP.md` for full task→tool mapping.

---

## CAPTCHA / bot check — active wait (do not stop agent or browser)

After **every** navigate and snapshot, scan for:

| Signal | Example |
|--------|---------|
| URL | `/sorry/`, `captcha`, `challenge` |
| Snapshot text | "I'm not a robot", "unusual traffic", "verify you're human", "Just a moment" |
| Elements | reCAPTCHA checkbox, iframe challenge |

**When detected:**

- **Pause** new navigations — do not open other URLs
- **Do not** stop the agent turn or close the browser
- Notify user once; then **poll until clear**

### Backoff schedule

| Round | Wait |
|-------|------|
| 1 | 60 s |
| 2 | 60 s |
| 3+ | Double (120 → 240 → 480 … max 3600 s) |

Use `node scripts/poll_captcha.mjs` (keeps MCP session alive) or `browser_wait_for` + `browser_snapshot` in a loop.

Auto-resume the **same URL** when snapshot shows CAPTCHA gone. Do not require user to say "continue".

---

## Agentic vs batch automation

Investigations must **not** use Node heredocs, shell loops, or scripts that call MCP for many URLs in one run. The agent calls tools one at a time with snapshot reasoning between steps.

See `SKILL.md` → "Agentic browsing rules".

---

## Login / CAPTCHA handling (legacy short form)

1. `browser_snapshot` — detect login wall, CAPTCHA, "verify you're human"
2. **Stop everything** — no new URLs
3. Tell user to fix in visible browser window
4. Wait indefinitely until user confirms
5. `browser_snapshot` again on **same page**; proceed

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login every session | Same `--user-data-dir`; no `--isolated`; don't delete profile dir |
| LinkedIn "Join" page | User not logged in — run Session 0 |
| MCP tools missing | Cursor Settings → MCP → enable playwright → reload |
| Chrome not found (Arch) | Use `--browser=chromium` |
| Screenshot write denied | Add `--allow-unrestricted-file-access` |
| Agent ran node MCP scripts | Wrong — agent must use MCP tools directly, one URL at a time |
| Agent skips posts, jumps URLs | Wrong — complete LinkedIn harvest checklist before next link |
| CAPTCHA visible but agent continues | Wrong — pause navigations, run poll loop, keep browser open |
| Agent ends turn waiting for "continue" | Wrong — auto-resume when CAPTCHA clears |

---

## Legal & ethics

Collect only publicly available information with appropriate authorization. Phase 0 in `SKILL.md` is mandatory.
