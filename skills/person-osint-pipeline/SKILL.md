---
name: person-osint-pipeline
description: >-
  Multi-phase person OSINT investigation. Agent browses via Playwright MCP (Google,
  every SERP hit, social harvest). CLI tools: SpiderFoot, Sherlock, Holehe; browser:
  Epieos, IntelTechniques, Overpass. All usernames/emails cross-verified via face
  pipeline before attribution. Supports Mode B hypothesis discovery without initial
  name/face. Requires authorization.
---

# Person OSINT Pipeline

Given **subject name** + **reference photo**, produce verified social accounts, pruned face assets, article findings, social network metadata, location inference, and `final_report.md` — all under `{cwd}/{subject_slug}_osint/`.

---

## Who does what (CRITICAL)

| Actor | Responsibility |
|-------|----------------|
| **You (the agent)** | ALL browser work via Playwright MCP tools — navigate, click, scroll, snapshot, screenshot, read pages like a human |
| **You (VLM)** | Face-visible checks, metadata extraction, location inference |
| **Python scripts** | `init_workspace.py`, `verify_accounts.py`, `prune_faces.py`, `build_social_graph.py`, `log_step.py`, `init_hypothesis_workspace.py`, tool wrappers — never browser automation loops |

### Investigation modes

| Mode | Input | Doc |
|------|-------|-----|
| **A — Known subject** | Name + reference photo | Phases 0–11 |
| **B — Hypothesis** | Org/country/threat hypothesis | `docs/HYPOTHESIS_DISCOVERY_MODE.md` |

### OSINT tool docs (read before using tools)

| Doc | Content |
|-----|---------|
| `docs/OSINT_TOOLS.md` | Full tool chain order |
| `docs/SPIDERFOOT.md` | SpiderFoot CLI/UI — **no MCP** |
| `docs/CROSS_VERIFICATION.md` | Username/email must be face-verified |
| `docs/RUN_LOGGING.md` | Log every step to `OSINT_RUN_LOG.md` |
| `docs/HYPOTHESIS_DISCOVERY_MODE.md` | Mode B iterative loop |

---

### NEVER do these

- Run `node run_osint_mcp.mjs`, `run_full_osint.mjs`, or any JS that calls MCP on your behalf
- Write `node << 'EOF'` heredocs or any loop that batch-navigates multiple URLs without your reasoning between each
- Write standalone Playwright `.js` / `.mjs` browser automation files for investigations
- Use `WebFetch` or `curl` instead of Playwright MCP for profile pages
- Use the VLM for face **identity** matching scores (scripts only)

If Playwright MCP tools are unavailable, **STOP** and tell the user to enable `playwright` in MCP settings (see `reference.md`). Do not work around with scripts.

---

## Agentic browsing rules (READ BEFORE EVERY MCP CALL)

You are a **human-like investigator** using a **visible headed browser** — not a scraper looping URLs. The user attached MCP specifically so you **stay on one page and go deep**.

### One URL at a time — finish before leaving

| Wrong (robot) | Right (agentic) |
|---------------|-----------------|
| Visit LinkedIn → screenshot → immediately open GitHub → PyPI → next | Open **each Google SERP hit** → **complete entire harvest** → back to SERP → next hit |
| Batch 10 URLs in one script/loop | One MCP tool call → read snapshot → decide next action → repeat **on same page** |
| Start with `site:linkedin.com` dorks | **Session A:** plain Google name search first; dorks only in Session B |
| `node -e` / heredoc loops calling MCP for many URLs | **You** call each MCP tool yourself, one step at a time, with reasoning between steps |

**Hard rule:** Do not navigate away from a profile/article until that item's harvest checklist (below) is complete.

### CAPTCHA / bot check — pause progress, keep agent + browser alive

After **every** `browser_navigate` and **every** `browser_snapshot`, check for bot walls.

**If ANY of these appear — pause investigation progress (do not open new URLs):**

- "I'm not a robot" / reCAPTCHA checkbox
- "unusual traffic" / `/sorry/` in URL
- "verify you're human" / "security check"
- Cloudflare "Just a moment"
- Login wall when session should be active

**When detected — the agent does NOT stop or end its turn. It waits actively:**

1. **Do not** navigate to another URL or continue discovery/harvest on other pages
2. Tell the user once: *"Bot check on [URL]. Please solve it in the browser window. I am waiting and keeping the browser open."*
3. **Keep the MCP daemon and browser window running** — never close the browser or exit the investigation loop
4. Enter the **CAPTCHA wait loop** (below) until the check clears
5. `browser_snapshot` — confirm CAPTCHA gone — **then** resume **the same URL** (not the next one)

**Do not** wait for the user to type "continue" before resuming. Auto-resume as soon as the snapshot shows the CAPTCHA is gone.

#### CAPTCHA wait loop (mandatory backoff)

The agent must **stay running** and poll — not halt the session or disconnect MCP.

| Round | Wait before next snapshot check |
|-------|----------------------------------|
| 1 | 60 seconds |
| 2 | 60 seconds |
| 3+ | Double previous wait (120s → 240s → 480s → … cap 3600s) |

Each round:

1. Log: `CAPTCHA_WAIT round=N wait_sec=X`
2. Wait (keep browser alive — use `poll_captcha.mjs` or `browser_wait_for` `{time: N}` on the **same MCP session**)
3. `browser_snapshot` → re-check CAPTCHA signals
4. If clear → resume same URL immediately
5. If still blocked → next round with updated wait

**Preferred:** run the helper (keeps one MCP connection open during waits):

```bash
node scripts/poll_captcha.mjs
```

**Alternative:** call `browser_wait_for` with `{ "time": 60 }` then `browser_snapshot` in the same agent loop — do **not** end your turn between rounds.

**Never:**

- Close the browser or stop the MCP daemon during CAPTCHA wait
- End the agent turn and tell the user "I'll wait for you to say continue"
- Navigate to a different URL while CAPTCHA is visible
- Hit the next Google query or next profile while blocked

This applies to Google, LinkedIn, Instagram, and every other site.

### Pacing (human-like)

- `browser_snapshot` → read → decide → one action (click, scroll, screenshot)
- Pause 2–5 s between major navigations
- **Scroll:** `browser_press_key` with `PageDown` / `End` — there is **no** `browser_scroll` (see `MCP_TOOL_MAP.md`)
- Click "Load more" / "Show more posts" when snapshot shows those refs (`browser_click`)

### What feels agentic vs robotic

| Robotic | Agentic |
|---------|---------|
| Single shell script loops 20 URLs | Agent reads snapshot: "I see post 3 of 12, scrolling" |
| Same timing every action | Agent adapts: expand truncated posts, open media lightbox |
| Skip posts when no face in thumbnail | Open post, check full view, then decide |
| Ignore CAPTCHA, hit next Google query | Pause progress, poll with backoff, keep browser open |

---

## Session 0 — Persistent login (run ONCE per machine)

LinkedIn and Instagram require a logged-in browser. The user signs in **once**; sessions persist forever via `--user-data-dir`.

### MCP config (must be set before asking user to log in)

Project `.cursor/mcp.json` (or `~ /.codex/mcp.json`):

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

| Flag | Purpose |
|------|---------|
| **No `--headless`** | Real visible browser window |
| **`--user-data-dir`** | Fixed path — cookies/sessions survive Cursor restarts, agent sessions, reboots |
| **No `--isolated`** | Never use — that wipes sessions on close |
| **`--allow-unrestricted-file-access`** | Screenshots can write to workspace |

Profile path: `~/.cursor/playwright-osint-profile` (create automatically on first run).

### Agent steps before login prompt

**Do not use MCP to open login pages** — the browser closes when the agent disconnects.

Tell the user to run in a terminal (20-minute window):

```bash
cd skills/person-osint-pipeline/scripts && ./login_setup.sh
```

After they say **"logged in"**, start investigations with `start_mcp_daemon.sh` + MCP url config.

When CAPTCHA / 2FA appears mid-investigation: enter CAPTCHA wait loop (60s → 60s → double); keep browser open; auto-resume when clear.

---

## Prerequisites

1. Playwright MCP connected with persistent profile (Session 0 complete)
2. Browsers: `npx @playwright/mcp install-browser firefox`
3. Python venv: `cd scripts && ./setup_venv.sh`
4. VLM-capable agent (you)
5. User provides: **full name**, **reference photo** (clear frontal portrait), **authorization**

```bash
eval "$(bash scripts/resolve_paths.sh)"
# SKILL_SCRIPTS and PYTHON are set
```

---

## Phase 0 — Authorization (MANDATORY)

Confirm `authorized_by` and `purpose`. Refuse harassment/stalking. Record in `accounts_index.md` header.

For **Mode B** (hypothesis / threat intel): also record scope and use `init_hypothesis_workspace.py`. See `docs/HYPOTHESIS_DISCOVERY_MODE.md`.

---

## Phase 0.5 — Install OSINT tools (agent runs if missing)

Before SpiderFoot / Sherlock / Holehe:

```bash
cd skills/person-osint-pipeline/scripts
./install_osint_tools.sh
eval "$(bash resolve_paths.sh)"
```

Verify: `test -f "$SPIDERFOOT_SF"` and `$VENV/bin/sherlock --version`.

**Log:** `log_step.py --phase 0-tools --step "install_osint_tools" --status ok`

If install fails: log `fail`, document error in run log, continue with Playwright-only phases.

---

## Workspace setup

```bash
$PYTHON $SKILL_SCRIPTS/init_workspace.py \
  --subject-name "{Full Name}" \
  --reference-photo "/abs/path/reference.jpg" \
  --cwd "{cwd}" \
  --authorized-by "{authorized_by}" \
  --purpose "{purpose}"
```

Creates `{cwd}/{subject_slug}_osint/` with `reference.jpg`, `accounts_index.md`, `identifiers_index.md`, and dirs: `accounts/`, `articles/`, `related/`, `locations/`, `network/`, `tools/`.

**Log every setup step** — see `docs/RUN_LOGGING.md`.

---

## Phase 1 — Session A: Plain Google name search (FIRST — mandatory)

**Do NOT use Google dorks (`site:linkedin.com`, etc.) in Session A.**  
Type the person's **full name** in Google like a human, then open **each organic result** one by one.

This is what the user expects instead of jumping straight to platform-specific dorks.

### 1A-1 — Search like a human

1. `browser_navigate` → `https://www.google.com`
2. `browser_snapshot` → CAPTCHA check → if blocked, **STOP** and wait for user
3. `browser_click` → Google search box (ref from snapshot)
4. `browser_type` → `{ "text": "{Full Name}", "submit": true }`
5. `browser_snapshot` → read **every organic result** (title + URL)

### 1A-2 — Visit EACH hit before the next (combined discover + harvest)

For **each result link** on page 1 (then page 2 if needed):

1. Note URL + title in snapshot
2. `browser_click` result **or** `browser_navigate` to that URL
3. `browser_snapshot` → CAPTCHA check
4. **Classify:** social profile | article | repo | irrelevant
5. **Deep harvest immediately** (do not return to Google until this URL is finished):
   - **Social:** run full Phase 2 checklist below (profile, scroll all posts, screenshots)
   - **Article/repo:** write `articles/{slug}.md`, screenshot if useful
   - **Irrelevant:** mark REJECTED, leave
6. Record in `accounts_index.md` or `articles_index.md`
7. `browser_navigate_back` **or** re-open Google SERP for the same query
8. Continue to **next result** on the same SERP page
9. When page exhausted: `browser_click` "Next" → repeat

**Hard rule:** Never skip to dork queries until every plausible Session A SERP hit is opened and harvested.

### 1A-3 — Reverse image (after name SERP pass)

1. Google Images → `browser_file_upload` reference photo
2. For each similar-result link: open → harvest like 1A-2

---

## Phase 1 — Session B: Google dorks (SECOND pass only)

Run **only after Session A is complete.** Purpose: find additional URLs not in Session A SERP.

| Dork query |
|------------|
| `site:linkedin.com/in "{name}"` |
| `site:instagram.com "{name}"` |
| `site:github.com "{name}"` |
| `site:x.com "{name}"` |
| `"{name}" interview OR article OR hackathon OR paper` |

For each **new** URL not already in index: open → deep harvest → record.  
Skip URLs already harvested in Session A.

---

## Phase 2 — Deep harvest (ONE account at a time)

Pick the **first** `CANDIDATE` row. Complete **entire** checklist below. Set `HARVESTED`. Only then open the next row.

**Never** have two profile tabs half-finished. One URL, full depth, then next.

### CAPTCHA gate (every step)

Before screenshot, scroll, or click: `browser_snapshot`. If bot check → STOP entire pipeline, wait for user.

### LinkedIn — full harvest checklist

For `{handle_dir}_linkedin`:

1. `browser_navigate` → profile URL → snapshot (CAPTCHA check)
2. `browser_take_screenshot` → `accounts/{handle_dir}/profile.png`
3. **VLM:** face visible in profile shot? Record URL in `image_links`
4. **Activity / posts section** — repeat until no new content:
   - `browser_press_key` `PageDown` (or click "Show all activity")
   - `browser_snapshot` — identify each post with media or face
   - For each post: click/open if needed → `browser_take_screenshot` → `{url_slug}.png`
   - **VLM:** face visible? Keep + append post URL to `image_links`
   - Click "Load more" / scroll again if snapshot shows more posts
5. Optional: Experience, Education, Projects — `browser_snapshot` excerpts for Phase 5
6. Mark row `HARVESTED` in `accounts_index.md`
7. **Now** proceed to next candidate

### Instagram — full harvest checklist

1. Navigate → profile → `profile.png` + VLM
2. Scroll **entire** grid / reels / tagged photos
3. Each face-visible item → screenshot + URL in `image_links`
4. Stories/highlights if accessible
5. Mark `HARVESTED` → next candidate

### X / Facebook / other social

Same pattern: profile first → scroll all posts → screenshot faces → complete before leaving.

### Articles / non-social (one at a time)

1. Navigate → CAPTCHA check
2. `browser_snapshot` → write full `articles/{slug}.md`
3. Screenshot if page has subject photos (VLM gate)
4. Mark done → next article

**Phase 2 complete when:** every row is `HARVESTED` or `REJECTED` with no skipped posts on social profiles.

---

## Phase 3 — Face verification (script)

```bash
$PYTHON $SKILL_SCRIPTS/verify_accounts.py \
  --workspace {workspace} --reference reference.jpg --threshold 0.45
```

- ≥1 face match → `VERIFIED`, directory kept
- No match → `REJECTED`, directory **deleted**, row removed from accounts_index
- **Do not use VLM for matching scores**

---

## Phase 4 — Face pruning (script)

```bash
$PYTHON $SKILL_SCRIPTS/prune_faces.py \
  --workspace {workspace} --reference reference.jpg --match-threshold 0.45
```

- Subject-matching faces stay in `accounts/{handle}/`
- Other detected faces → moved to `related/`
- No face detected → deleted from account dirs

---

## Phase 3.5 — Extract identifiers (after first verify pass)

From **VERIFIED** accounts and harvested articles:

1. Usernames (GitHub handle, IG handle, etc.) → `identifiers_index.md` as `CANDIDATE`
2. Emails (bios, contact, SpiderFoot later) → `CANDIDATE`
3. Domains (personal sites) → seed for SpiderFoot

**Do not** run Sherlock/Holehe on CANDIDATE identifiers until at least one is tied to a VERIFIED account OR explicitly cross-linked in source text.

---

## Phase 9 — OSINT tool enrichment (CLI + browser)

**Read `docs/OSINT_TOOLS.md` and `docs/CROSS_VERIFICATION.md` first.**

### 9a — Sherlock (verified usernames only)

```bash
./run_sherlock.sh --workspace {workspace} --username {verified_handle}
```

For each `Found` URL with a **person profile**: Playwright harvest → face verify → update `identifiers_index.md`.

### 9b — Holehe (verified or LinkedIn-listed emails)

```bash
./run_holehe.sh --workspace {workspace} --email {email}
```

### 9c — Epieos (Playwright MCP)

1. `browser_navigate` → `https://epieos.com/`
2. Enter email → snapshot results
3. Save to `tools/epieos/{email_slug}.md`
4. If Google profile photo shown → screenshot → face verify

### 9d — SpiderFoot (primary aggregator)

**Read `docs/SPIDERFOOT.md`.** No MCP — use terminal:

```bash
./run_spiderfoot.sh \
  --workspace {workspace} \
  --target "{email_or_username_or_domain}" \
  --target-type EMAILADDR \
  --use-case passive
```

Target types: `EMAILADDR`, `USERNAME`, `INTERNET_NAME`, `DOMAIN_NAME`, `HUMAN_NAME`, `IP_ADDRESS`.

Parse `tools/spiderfoot/*/results.json` → new candidates → **return to Playwright harvest + Phase 3 verify**.

### 9e — IntelTechniques (Playwright)

Navigate Michael Bazzell's search forms for email/username/phone; record hits in `tools/inteltechniques/`.

### 9f — Iteration loop

```
Tool output → CANDIDATE identifiers → Playwright profile harvest → face verify
  → VERIFIED seeds → re-run SpiderFoot/Sherlock → new candidates → repeat
```

Stop when no new VERIFIED identifiers for 2 iterations. Log each cycle: `--phase T-iterate-N`.

---

## Phase 10 — Relationships, orgs, projects

For verified subject (Mode A) or HIGH-confidence candidates (Mode B):

1. Scrape LinkedIn Experience, Education, Projects (MCP)
2. Build `network/org_graph.csv`: `person_a,person_b,relation,org,source_url`
3. Google co-affiliation queries: `"{name}" "{org}"`, `"{name}" co-author`
4. SpiderFoot on institutional **domains** (passive)
5. VLM synthesis: `relationships_synthesis.md` — who they work with, project involvement, org ties

**Threat intel framing:** cite only **public sources** in `evidence_index.md`; state confidence LOW/MEDIUM/HIGH.

---

## Phase 11 — Geolocation (Overpass + VLM)

Not live tracking — infer from images and posts:

1. **Overpass Turbo** (Playwright): query OSM for landmarks seen in photos
2. VLM on subject images + network location context (Phase 7)
3. Write `locations/subject_synthesis.md` with explicit confidence

---

## Phase 5 — Metadata scrape (agent + MCP, VERIFIED only)

For each **VERIFIED** account:

1. `browser_navigate` → profile URL
2. `browser_snapshot` (+ screenshots if DOM incomplete)
3. Write `accounts/{handle_dir}/account.md` from `templates/account_profile.md.tpl`:
   - Bio, headline, location, website
   - Every post: URL, date, caption, location tag, song/audio, mentions, engagement, other metadata
4. Also scrape **verified LinkedIn and X** fully before location phase

---

## Phase 6 — Instagram network (VERIFIED Instagram only)

1. Open followers + following lists via MCP; scroll to load
2. Append to `network/social_graph.csv`:

```csv
username,relation,profile_url,display_name
```

3. `$PYTHON $SKILL_SCRIPTS/build_social_graph.py --workspace {workspace}`
4. For each network user (cap 50–100):
   - `network/{username}/account.md` — **text/metadata only, no face screenshots**
   - Visit profile via MCP; scrape posts (caption, location, song, etc.)

---

## Phase 7 — Location inference (VLM)

### 7a — Per follower/following

For each `network/{username}/account.md` → prompt VLM → write `locations/{username}.md`:
> Given these posts, what locations can you infer or that are explicitly stated?

### 7b — Per subject image

For each image in verified `accounts/{handle}/` → prompt VLM with image + network location context:
> Given this image and the network location data, where was this taken or where is the subject from?

Append to `locations/subject_images.md`.

### 7c — Synthesis

Feed LinkedIn, X, Instagram `account.md` files + all `locations/*.md` → VLM → `locations/subject_synthesis.md`:
> Where is the subject from? Where were posts taken? What else can you infer?

---

## Phase 8 — Final report

Compile `final_report.md` from `templates/final_report.md.tpl`.

---

## File naming rules

| Artifact | Rule |
|----------|------|
| Workspace | `{subject_slug}_osint/` in user CWD |
| Account dir | Handle only: `janedoe_ig`, `jane-doe_linkedin` |
| Profile shot | Always `profile.png` |
| Post shots | `{url_slug}.png` from post/media URL |
| `image_links` column | Semicolon-separated source URLs for every saved screenshot |

---

## Completion checklist

- [ ] Session 0: persistent login configured and verified
- [ ] Phase 0 authorization recorded
- [ ] Phase 1 Session A: plain Google name search — **each SERP hit opened and harvested**
- [ ] Phase 1 Session B: dorks only after Session A (new URLs only)
- [ ] Phase 2: **each** social profile fully harvested (all posts scrolled) before next URL
- [ ] CAPTCHA waits honored — active poll loop, browser kept open, auto-resume when clear
- [ ] No batch MCP scripts used — agent called tools step-by-step
- [ ] `verify_accounts.py` + `prune_faces.py` succeeded
- [ ] Verified `accounts/*/account.md` complete
- [ ] `network/social_graph.csv` + network MDs (if IG verified)
- [ ] `locations/` written
- [ ] Phase 0.5: OSINT tools installed (`install_osint_tools.sh`)
- [ ] Phase 9: Sherlock/Holehe/SpiderFoot run on **verified** seeds only; outputs cross-verified
- [ ] `identifiers_index.md` maintained; no unverified attribution
- [ ] `OSINT_RUN_LOG.md` updated every run (`log_step.py`)
- [ ] Phase 10: relationships/org graph (if scope requires)
- [ ] Phase 11: location synthesis with confidence levels

See `reference.md` for MCP tool cheat sheet, `MCP_TOOL_MAP.md` for task→tool mapping, and troubleshooting.
