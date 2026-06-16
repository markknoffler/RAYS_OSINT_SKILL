---
name: person-osint-pipeline
description: >-
  Multi-phase person OSINT investigation using Playwright MCP for social media
  discovery and screenshots, local InsightFace scripts for face verification, and
  VLM prompts for metadata extraction and location inference. Use when the user
  provides a subject name and reference photo and wants structured OSINT artifacts
  in the current working directory. Requires written authorization and legitimate
  purpose. Activates for person OSINT, social media investigation, face verification
  pipeline, or Playwright-based profile harvesting.
---

# Person OSINT Pipeline

Orchestrates a **phased investigation** from subject name + reference photo to verified accounts, pruned face assets, social network metadata, and location synthesis.

## Prerequisites

Before starting:

1. **Playwright MCP** running (`@playwright/mcp@latest`) — see repo `.cursor/mcp.json`
2. **Python venv** for face scripts:
   ```bash
   cd skills/person-osint-pipeline/scripts && ./setup_venv.sh
   ```
3. **VLM-capable agent** (Claude, Codex, Hermes, etc.) for face-visible checks and metadata extraction
4. User provides: **full name**, **reference photo path**, confirmation of **authorization**

Script path (adjust to your install):

```
SKILL_SCRIPTS=/path/to/RAYSpy-OSINT/skills/person-osint-pipeline/scripts
PYTHON=$SKILL_SCRIPTS/.venv/bin/python
```

---

## Phase 0 — Authorization gate (MANDATORY)

**Do not proceed** without explicit confirmation:

- Who authorized this investigation (`authorized_by`)
- Legitimate purpose (`purpose`): e.g. self-investigation, employer security with scope, journalism with consent, missing persons with family authorization
- **Refuse** harassment, stalking, non-consensual surveillance, or any illegal scope

Ask the user directly if not stated. Record answers in `accounts_index.md` header.

---

## Workspace setup

In the user's **current working directory** (`{cwd}`), create:

```
{cwd}/{subject_slug}_osint/
```

Use `subject_slug` = lowercase name with underscores (e.g. `jane_doe` → `jane_doe_osint`).

Copy the reference photo to `{workspace}/reference.jpg`.

Initialize `accounts_index.md` from template `templates/accounts_index.md.tpl` with Phase 0 metadata filled in.

Create empty directories: `accounts/`, `related/`, `locations/`, `network/`.

---

## Phase 1 — Discovery (Playwright MCP)

1. Ensure Playwright MCP server is started (Cursor: MCP → Start `playwright`)
2. Search the subject name on:
   - Instagram
   - LinkedIn (`site:linkedin.com/in`)
   - X / Twitter
   - Facebook
   - Google web search as fallback
3. For each **plausible** profile URL found, append a row to `accounts_index.md`:

| platform | profile_url | handle_dir | verification_status | image_links |
| --- | --- | --- | --- | --- |
| instagram | https://... | `{handle}_ig` | CANDIDATE | — |

**Handle directory naming:** derive from URL only (e.g. `janedoe_ig`), never the full URL. Use the same rules as `scripts/utils/image_naming.py` → `extract_handle_from_url()`.

**Do not** create `accounts/{handle}/` directories yet.

---

## Phase 2 — Screenshot harvest (Playwright MCP + VLM)

For each `CANDIDATE` row:

1. Navigate to `profile_url` with Playwright MCP
2. Screenshot profile picture → save as `accounts/{handle_dir}/profile.png`
3. Scroll posts, stories (if accessible), and media grid:
   - For each media item, take a screenshot
   - **VLM check** (you, not a script): *"Does this screenshot contain at least one clearly visible human face?"*
   - If **yes**: save file as `{url_slug}.png` where slug comes from the post/media URL (not `profile.png`)
   - Append the **source URL** to `image_links` column (semicolon-separated) and to the Image link log section
4. Update status to `HARVESTED` after screenshots saved

**Naming rules:**
- Profile only: `profile.png`
- All other images: sanitized URL slug + `.png`
- Directory name: handle only (`janedoe_ig`)

---

## Phase 3 — Account verification (script — NOT VLM)

Run local face matching. **Do not** use the LLM/VLM for identity matching scores.

```bash
$PYTHON $SKILL_SCRIPTS/verify_accounts.py \
  --workspace {workspace} \
  --reference reference.jpg \
  --threshold 0.45
```

- Accounts with **≥1** image matching reference → `VERIFIED`, directory kept
- Accounts with **no** match → `REJECTED`, directory **deleted**
- Read `scripts_log.txt` and updated `accounts_index.md`
- **Ignore REJECTED accounts** in all subsequent phases

---

## Phase 4 — Face pruning (script)

```bash
$PYTHON $SKILL_SCRIPTS/prune_faces.py \
  --workspace {workspace} \
  --reference reference.jpg \
  --match-threshold 0.45
```

- Subject-matching images stay in `accounts/{handle}/`
- Other images with detectable faces → moved to `related/`
- Images with no detectable face → deleted from account dirs

Confirm `related/` exists and verified dirs contain only subject-matched faces.

---

## Phase 5 — Profile metadata scrape (Playwright + VLM)

For each **VERIFIED** account only:

1. Re-open profile with Playwright MCP
2. Extract into `accounts/{handle_dir}/account.md` using `templates/account_profile.md.tpl`:
   - Bio, headline, location field, website
   - Pinned posts
   - Each post: URL, date, caption, location tag, song/audio, mentions, engagement
3. Use VLM on page screenshots if DOM text is incomplete

---

## Phase 6 — Instagram social network (VERIFIED IG only)

If a **verified Instagram** account exists:

1. Open followers and following lists (scroll with Playwright; use logged-in session if needed — see `reference.md`)
2. Append rows to `network/social_graph.csv`:

```csv
username,relation,profile_url,display_name
friend123,follower,https://instagram.com/friend123,Jane Friend
```

3. Run dedupe script:

```bash
$PYTHON $SKILL_SCRIPTS/build_social_graph.py --workspace {workspace}
```

4. For each network user (cap **50–100** unless user requests more):
   - Create `network/{username}/account.md` — **text/metadata only, no face screenshots**
   - Visit profile; scrape posts for captions, locations, songs, tags into that MD file

---

## Phase 7 — Location extraction (VLM prompts)

### 7a — Per network user

For each `network/{username}/account.md`, prompt your VLM:

> Given the following post and profile text for user @{username}, list every **explicit** location mentioned and every **inferred** location with reasoning. Output as markdown tables.

Write result to `locations/{username}.md` using `templates/locations_per_user.md.tpl`.

### 7b — Per subject post image

For each image in verified `accounts/{handle}/` (except profile if redundant):

Prompt VLM with:
- The image
- Subject's `account.md` content from all verified platforms
- All `locations/*.md` from network users

> Given this image of the subject, their verified profile content, and location context from their Instagram network, where was this photo likely taken? State confidence (high/medium/low) and evidence.

Append findings to `locations/subject_images.md` (one section per image filename).

### 7c — Cross-platform synthesis

Feed organized content from LinkedIn, X, and Instagram `account.md` files plus all `locations/*.md` to VLM:

> Synthesize where the subject lives, works, travels, and socializes. Separate stated vs inferred. Note confidence.

Write to `locations/subject_synthesis.md`.

---

## Phase 8 — Final report

Compile `final_report.md` from `templates/final_report.md.tpl` including:

- Verified vs rejected accounts
- Location assessment (home, travel, per-image table)
- Social network summary
- Related faces count (`related/`)
- Confidence and limitations

**Completion checklist:**

- [ ] Phase 0 authorization recorded
- [ ] `accounts_index.md` complete
- [ ] `verify_accounts.py` and `prune_faces.py` ran successfully
- [ ] Verified `accounts/*/account.md` filled
- [ ] `related/` populated (if applicable)
- [ ] `network/social_graph.csv` + network MD files (if IG verified)
- [ ] `locations/` files written
- [ ] `final_report.md` delivered

---

## VLM prompt — face visible check (Phase 2)

Use for each post/media screenshot before saving:

> Look at this screenshot from a social media profile. Does it contain at least one clearly visible human face (not just icons, logos, or distant crowds)? Answer YES or NO only, then one sentence describing what you see.

Only save the screenshot if YES.

---

## Important constraints

- **Never** use VLM for numeric face identity matching — only `verify_accounts.py` / `prune_faces.py`
- **Never** commit investigation workspaces to git
- Respect platform rate limits; add delays between navigations
- If follower lists are login-walled, document limitation in `final_report.md` and skip Phase 6 partial steps

See `reference.md` for platform limits, Playwright session setup, and troubleshooting.
