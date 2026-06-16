# Sample investigation workspace

When an agent runs the **person-osint-pipeline** skill, it creates a workspace like this in the user's current working directory:

```
jane_doe_osint/
├── reference.jpg              # User-supplied reference photo (copy)
├── accounts_index.md          # Master manifest: links, handles, status
├── accounts/
│   ├── janedoe_ig/            # Handle only — not full URL
│   │   ├── profile.png        # Profile screenshot (fixed name)
│   │   ├── p_abc123xyz.png    # Post screenshots named from URL slug
│   │   └── account.md         # Scraped bio/posts (Phase 5)
│   └── janedoe_linkedin/
├── related/                   # Non-subject faces from verified accounts
├── locations/
│   ├── friend_user.md
│   └── subject_synthesis.md
├── network/
│   ├── social_graph.csv
│   └── friend_user/
│       └── account.md         # Text only — no face screenshots
├── scripts_log.txt
└── final_report.md
```

## accounts_index.md status values

| Status | Meaning |
|--------|---------|
| `CANDIDATE` | URL found in Phase 1, not yet screenshotted |
| `HARVESTED` | Screenshots collected, pending verification |
| `VERIFIED` | At least one face matched reference (script pass 1) |
| `REJECTED` | No face match — directory deleted |

## Script invocation (from skill scripts dir)

```bash
.venv/bin/python verify_accounts.py --workspace /path/to/jane_doe_osint --reference reference.jpg
.venv/bin/python prune_faces.py --workspace /path/to/jane_doe_osint --reference reference.jpg
.venv/bin/python build_social_graph.py --workspace /path/to/jane_doe_osint
```
