# RAYSpy-OSINT — Project Context & Decision Log

Living document for agents and humans. Updated as the skill evolves.

---

## 1. What this codebase is

**RAYSpy-OSINT** (`RAYS_OSINT_SKILL/`) is a **separate git repo** from the RAYSpy 3D globe app. It contains:

| Path | Purpose |
|------|---------|
| `skills/person-osint-pipeline/SKILL.md` | Agent orchestration — the agent browses via Playwright MCP |
| `skills/person-osint-pipeline/scripts/` | Python only: face verification, workspace init, graph dedupe |
| `skills/person-osint-pipeline/templates/` | Markdown templates for artifacts |
| `skills/person-osint-pipeline/reference.md` | MCP config, troubleshooting |
| `.cursor/mcp.json` (in parent RAYSpy workspace) | Playwright MCP server config |

**Goal:** Given a person's **name + reference photo**, produce structured OSINT artifacts in `{cwd}/{subject_slug}_osint/`:

- Social profile links + per-account image directories
- Face-verified accounts only (InsightFace scripts)
- Article/web findings
- Profile metadata markdown
- Instagram follower/following network (if verified IG)
- Location inference via VLM
- `final_report.md`

---

## 2. What the user originally asked for (source prompt)

The user designed a multi-phase pipeline:

1. User gives **name + picture**
2. **Agent** starts Playwright MCP and searches Google / platforms for the person
3. For **every link found** (social + articles): open it, screenshot, decide text vs image content
4. On social accounts: screenshot profile, then every post/story with a **visible face** (VLM gate)
5. Create `accounts_index.md` with: platform, URL, handle directory name, image source URLs
6. Directory per account = **handle only** (e.g. `samreedh-bhuyan_linkedin`), not full URL
7. Images: `profile.png` for profile; all others named from post URL slug
8. Run **face recognition script** (not VLM) — delete accounts with zero face match
9. Run **prune script** — move non-subject faces to `related/`
10. Scrape verified accounts: bio, every post, captions, locations, songs, mentions
11. If verified Instagram: followers/following → CSV → visit each (text only, no face shots) → MD per user
12. VLM location inference using images + network context + LinkedIn/X/IG content
13. Final synthesis report

**Critical user requirement:** The **AI agent** must drive Playwright MCP directly like a human — **not** Node.js scripts that call MCP on the agent's behalf.

---

## 3. Conversation arc & user corrections

| # | User said | Implication |
|---|-----------|-------------|
| 1 | Can't use headless fetch for LinkedIn/Instagram | Need real headed browser + Playwright MCP |
| 2 | User must solve CAPTCHAs manually | Human-in-the-loop; agent pauses |
| 3 | Login once, persist forever | `--user-data-dir` with fixed path; never `--isolated` |
| 4 | Wants agentic browser, not scripts surfing | Deprecated `run_osint_mcp.mjs`, `run_full_osint.mjs` |
| 5 | Must find articles too, not just social | Phase 1d article discovery + `articles_index.md` |
| 6 | Test on Samreedh Bhuyan (self) with reference photo | Workspace: `test_investigation/samreedh_bhuyan_osint/` |
| 7 | Logged into Firefox personally | Asked if Playwright can reuse that Firefox profile |
| 8 | MCP closes too fast for 15-min login | Need standalone server instructions (Section 8) |
| 9 | This MD file as persistent context | This document |
| 10 | Agent jumps links, never deep-harvests LinkedIn posts | Phase 2: one URL at a time, full scroll/checklist |
| 11 | CAPTCHA must halt everything indefinitely | Stop all navigations until user says continue |
| 12 | Feels like scripts not agentic AI | Ban batch MCP loops; agent calls tools step-by-step |
| 13 | **Session 1 must NOT use Google dorks first** | Plain Google name search → open **each organic hit** → deep harvest before next |
| 14 | **Session 2 uses dorks** | Only after Session A complete; for URLs not already harvested |
| 15 | **`browser_scroll` does not exist** | Use `browser_press_key` PageDown/End; map in `MCP_TOOL_MAP.md` |
| 16 | Delete `test_investigation/` before fresh run | Keep root `2026-06-19-115018_hyprshot.png`; reference at `samreedh_reference.jpg` |
| 17 | **CAPTCHA: agent must not stop** | Pause progress only; poll 60s→60s→double; keep browser + MCP alive; auto-resume |

---

## 4. Key technical decisions

### 4.1 Agent vs scripts

| Task | Who |
|------|-----|
| Google search, open links, scroll, screenshot, metadata scrape | **Agent** via MCP tools |
| Face identity matching (numeric) | **`verify_accounts.py`** only |
| Face visible? (yes/no) | **Agent VLM** |
| Workspace init, graph dedupe | **Python scripts** |

**Why:** User explicitly wanted the LLM/VLM agent to browse. Scripts are offline, deterministic, and cheap for face math.

### 4.2 Headed browser, not headless

LinkedIn and Instagram show login walls and bot checks on headless automation.

**Decision:** Never pass `--headless` in MCP config.

### 4.3 Persistent sessions (`--user-data-dir`)

Playwright MCP supports three profile modes (from official docs):

| Mode | Flag | Behavior |
|------|------|----------|
| **Persistent** (default) | `--user-data-dir /fixed/path` | Cookies, logins survive restarts |
| Isolated | `--isolated` | Fresh session every time — **do not use** |
| Browser extension | `--extension` | Attach to running Chrome/Edge only — **not Firefox** |

**Decision:** Fixed profile at `~/.cursor/playwright-osint-profile` (or Firefox variant below).

Default without `--user-data-dir`: `~/.cache/ms-playwright/mcp-{channel}-{workspace-hash}` — works but hash changes per workspace. Custom path is clearer for OSINT.

### 4.4 Firefox vs Chromium vs your daily Firefox

**User question:** "I logged into Firefox already — can Playwright use that?"

**Answer: No — not directly.**

| Approach | Works? | Notes |
|----------|--------|-------|
| Point `--user-data-dir` at `~/.mozilla/firefox/*.default-release` | **No** | Firefox locks profile while your Firefox is open; Playwright launches separate process; format/lock conflicts |
| `--executable-path /usr/bin/firefox` + separate `--user-data-dir` | **Yes** | Uses Firefox binary but **dedicated** automation profile |
| `--browser=firefox` + new `--user-data-dir` | **Yes** | **Recommended** — log in once in Playwright's Firefox window |
| `--extension` with daily Firefox | **No** | Extension mode is Chrome/Edge only |

**Decision (2026-06-19):** Switch MCP to `--browser=firefox` with dedicated profile:

```
~/.cursor/playwright-osint-profile
```

User logs into LinkedIn/Instagram **once** in that Playwright Firefox window. Sessions persist across all future agent runs.

### 4.5 Self-investigation login

User is searching for **himself** (Samreedh Bhuyan). Logging into **his own** LinkedIn/Instagram in the Playwright profile is correct — needed for:

- Full profile view (not "Join LinkedIn" wall)
- Follower/following lists (Phase 6)
- Posts behind login

This is not "wrong account" — it's authenticated access to your own data for self-OSINT.

### 4.6 Arch Linux browser choice

- `--browser=chrome` failed: Chrome not at `/opt/google/chrome/chrome`
- `npx @playwright/mcp install-browser chrome-for-testing` works (fallback Chromium)
- User has system Firefox at `/usr/bin/firefox` — **preferred going forward**

### 4.7 Deprecated files

| File | Status | Reason |
|------|--------|--------|
| `scripts/run_osint_mcp.mjs` | Deprecated | Agent must call MCP directly |
| `scripts/run_full_osint.mjs` | Deprecated | Same |
| `scripts/test_mcp_discovery.mjs` | Dev only | Not for investigations |

See `scripts/DEPRECATED.md`.

### 4.8 Agentic browsing (not batch scripts)

Previous investigation runs incorrectly:

1. Used Node heredocs looping 10+ URLs in one shell command
2. Started with `site:linkedin.com` / `site:instagram.com` **dorks** instead of plain Google name search
3. Collected LinkedIn/Instagram URLs only without walking every SERP hit

That caused:

- LinkedIn: only `profile.png`, no post scroll (in early runs)
- Google CAPTCHA: agent moved to next query instead of stopping
- Robotic feel vs human investigator

**Correct behavior (now in SKILL.md):**

- **Session A (first pass):** `google.com` → type full name in search bar → click **each organic result** → deep harvest that URL → back to SERP → next hit
- **Session B (second pass):** Google dorks for supplemental URLs not found in Session A
- Scroll via `browser_press_key` (`PageDown` / `End`) — **no** `browser_scroll` tool
- CAPTCHA: pause navigations, **active poll loop** (60s → 60s → double), keep browser open, auto-resume when clear — agent never stops its turn
- Agent calls each MCP tool with snapshot reasoning — no automation loops

See `skills/person-osint-pipeline/MCP_TOOL_MAP.md` for full Playwright MCP tool inventory mapped to OSINT tasks.

---

## 5. What was built & changed (timeline)

### Initial skill pack

- `SKILL.md` phased pipeline (0–8)
- Python: `init_workspace.py`, `verify_accounts.py`, `prune_faces.py`, `build_social_graph.py`
- InsightFace `buffalo_l` for face verification
- Templates for `accounts_index.md`, `account.md`, `final_report.md`

### MCP config iterations

1. **v1:** `--headless --browser=chromium` — failed on LinkedIn (login wall)
2. **v2:** Removed `--headless`, added `--user-data-dir` — correct approach
3. **v3:** Tried `--browser=chrome` on Arch — failed (Chrome not installed)
4. **v4:** `--browser=chromium` — worked for navigation
5. **v5 (current):** `--browser=firefox` — matches user's installed browser

### Skill rewrites

- Added **Session 0** (persistent login before prompting user)
- Added **Phase 1d** (articles + web, not just social)
- Added **"Who does what"** table — agent vs scripts
- Marked Node MCP drivers as deprecated
- Added `articles_index.md.tpl`

### Test investigation: Samreedh Bhuyan

- Workspace: `test_investigation/samreedh_bhuyan_osint/`
- Reference photo: `reference.jpg` (face validated)
- Found: LinkedIn, GitHub (`markknoffler`), PyPI (`rays-core`)
- LinkedIn blocked without login (screenshot showed "Join LinkedIn")
- Face verify rejected profiles (no face in login-wall screenshots)
- Rich metadata from public LinkedIn index via web fetch
- Artifacts: `final_report.md`, `accounts_index.md`, `articles_index.md`

---

## 6. MCP configuration (current)

**File:** `/home/mark/Desktop/RAYSpy/.cursor/mcp.json`

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

| Flag | Why |
|------|-----|
| `--browser=firefox` | User's installed Firefox |
| `--user-data-dir` | One-time login persists forever |
| No `--headless` | Visible window for CAPTCHA/login |
| No `--isolated` | Would wipe sessions |
| `--allow-unrestricted-file-access` | Screenshots write to workspace |

Install Firefox for Playwright (once):

```bash
npx @playwright/mcp install-browser firefox
```

---

## 7. How Playwright MCP works (for this skill)

```
User → Cursor Agent → MCP tools (browser_navigate, browser_snapshot, ...)
                              ↓
                    Playwright MCP Server (npx @playwright/mcp)
                              ↓
                    Firefox (headed) with --user-data-dir profile
                              ↓
                    LinkedIn / Instagram / Google / ...
```

- Agent reads **accessibility snapshots** (structured YAML), not pixels — unless using `--caps=vision`
- Agent takes **screenshots** via `browser_take_screenshot` for face checks and harvest
- **One browser instance** per `--user-data-dir` — don't run two MCP servers on same profile

### MCP tools the agent uses

Full mapping: `skills/person-osint-pipeline/MCP_TOOL_MAP.md`

| Tool | Use |
|------|-----|
| `browser_navigate` | Open URLs, Google SERP |
| `browser_navigate_back` | Return to Google results after harvesting one hit |
| `browser_snapshot` | Read page structure, get click refs, CAPTCHA check |
| `browser_click` | Search results, pagination, load-more |
| `browser_type` | Type name into Google search box |
| `browser_press_key` | **Scroll** (`PageDown`, `End`) — replaces nonexistent `browser_scroll` |
| `browser_take_screenshot` | Save images to workspace |
| `browser_file_upload` | Reverse image search |
| `browser_tabs` | New tab while keeping context |
| `browser_wait_for` | Lazy-load pause |
| `browser_mouse_wheel` | Optional pixel scroll (`--caps=vision`) |

**Not available:** `browser_scroll`

---

## 8. Keeping the browser open for login (15+ minutes)

**Root cause:** When the agent (or a quick MCP client call) connects and disconnects, Playwright MCP **closes the browser** within seconds. That is why login feels impossible.

**Fix:** Use `login_setup.sh` — opens Firefox via Playwright **directly** (not MCP), keeps window open **20 minutes**, saves to the **same** persistent profile MCP uses later.

### One-time login (run in your terminal)

```bash
cd RAYS_OSINT_SKILL/skills/person-osint-pipeline/scripts
./login_setup.sh
```

- Firefox opens with LinkedIn + Instagram login tabs
- Window stays open **20 minutes** (set `LOGIN_MINUTES=30 ./login_setup.sh` for longer)
- Profile saved at: `~/.cursor/playwright-osint-profile`
- **Do not** run MCP server at the same time (same profile lock)

### After login — start MCP for investigations

Terminal 1 (keep open):

```bash
./start_mcp_daemon.sh
```

Cursor `.cursor/mcp.json` uses:

```json
{ "mcpServers": { "playwright": { "url": "http://localhost:8931/mcp" } } }
```

Reload Cursor → MCP → enable playwright.

### Persistence

| What | Where |
|------|-------|
| Cookies, logins | `~/.cursor/playwright-osint-profile/` |
| MCP config | `.cursor/mcp.json` → `url` mode + daemon |
| Never use | `--isolated` (wipes sessions) |

Log in once. All future `start_mcp_daemon.sh` + agent runs reuse the profile.

---

## 9. Why we cannot use your daily Firefox profile

Your Firefox profiles live at:

```
~/.mozilla/firefox/hld5icbh.default-release
~/.mozilla/firefox/4b8ojr8s.default
```

Playwright **cannot** safely attach to these because:

1. **Lock file** — Firefox refuses second instance on same profile
2. **Your Firefox is often open** — conflict guaranteed
3. **Browser extension mode** (`--extension`) does not support Firefox
4. **Risk** — automation could corrupt daily browsing data

**Correct workflow:** One-time login in Playwright's **separate** profile (`~/.cursor/playwright-osint-profile`). Same credentials, different browser profile.

---

## 10. Skill directory layout

```
RAYS_OSINT_SKILL/
├── PROJECT_CONTEXT.md          ← this file
├── README.md
├── .cursor/mcp.json            (symlink or copy in RAYSpy root)
└── skills/person-osint-pipeline/
    ├── SKILL.md                ← agent instructions
    ├── reference.md            ← MCP cheat sheet
    ├── scripts/
    │   ├── DEPRECATED.md
    │   ├── init_workspace.py
    │   ├── verify_accounts.py
    │   ├── prune_faces.py
    │   ├── build_social_graph.py
    │   └── utils/
    └── templates/
```

Agent skill installs:

```
~/.cursor/skills/person-osint-pipeline/
~/.codex/skills/person-osint-pipeline/
```

---

## 11. Known issues & open items

| Issue | Status | Next step |
|-------|--------|-----------|
| LinkedIn login wall without session | Blocked until Session 0 login | User logs in via Section 8 |
| Cursor MCP tools "Not connected" | Intermittent | Use HTTP server on :8931 or reload Cursor |
| Face verify rejects login-wall screenshots | Expected | Re-harvest after login |
| Google false-positive LinkedIn profiles | Agent must filter by name match | Improve Phase 1 filtering in SKILL |
| Instagram not found for Samreedh | May need login + reverse image | Re-run after Session 0 |
| Agent used Node MCP scripts earlier | Fixed in SKILL rewrite | Agent must use MCP tools only |

---

## 12. Next actions (fresh investigation workflow)

1. Ensure MCP daemon running (`start_mcp_daemon.sh` on :8931)
2. Delete prior `test_investigation/` (keep root hyprshot PNG)
3. Sync skill to `~/.cursor/skills/` and `~/.codex/skills/`
4. `init_workspace.py` with `samreedh_reference.jpg`
5. **Session A:** Plain Google `"Samreedh Bhuyan"` → each SERP hit → deep harvest
6. **Session B:** Dorks for new URLs only
7. `verify_accounts.py` + `prune_faces.py`
8. Metadata scrape, network graph, location inference, `final_report.md`

---

## 14. Latest session request (2026-06-19 continued)

**User asked:** Fix skill so agents do **not** jump straight to LinkedIn/Instagram dorks. Instead:

1. Google the person's **name** in the search bar (human-like)
2. Open **every** organic link from that SERP
3. Scroll and explore each link deeply before moving on
4. Use dorks only in a **later session** for supplemental discovery
5. Map all Playwright MCP tools to skill tasks (`MCP_TOOL_MAP.md`)
6. Document decisions in this file
7. Delete prior workspace, sync skill, re-run self-OSINT on Samreedh Bhuyan

**CAPTCHA clarification (2026-06-20):** "Halt" means **pause investigation progress**, not stop the agent or browser. When CAPTCHA appears:

- Agent **keeps running** and keeps MCP/browser alive
- Poll with backoff: **60s → 60s → double** (120, 240, 480…)
- Auto-resume when snapshot shows CAPTCHA cleared — no need for user to say "continue"
- Helper: `scripts/poll_captcha.mjs` (single long-lived MCP connection during waits)

**Technical decisions taken:**

| Decision | Rationale |
|----------|-----------|
| Split Phase 1 into Session A (plain name) + Session B (dorks) | Matches user's two-session mental model |
| Session A combines discover + harvest per hit | User wants each link explored when found |
| `browser_press_key` for scroll | No `browser_scroll` in Playwright MCP |
| `poll_captcha.mjs` for CAPTCHA waits | Keeps browser alive better than disconnecting `mcp_one.mjs` each minute |
| Reference photo | `samreedh_reference.jpg` was corrupt (SSL error screenshot); use portrait from hyprshot or user-provided image |

---

## 13. References

- Playwright MCP README: https://github.com/microsoft/playwright-mcp
- User profiles guide: https://microsoft-playwright-mcp.mintlify.app/guides/user-profiles
- Playwright docs MCP: https://playwright.dev/docs/getting-started-mcp
- `--user-data-dir` issues: https://github.com/microsoft/playwright-mcp/issues/136

---

*Last updated: 2026-06-26 — OSINT tool chain (SpiderFoot/Sherlock/Holehe), cross-verification, Mode B hypothesis, run logging.*
