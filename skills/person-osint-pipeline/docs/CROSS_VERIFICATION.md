# Cross-Verification — Usernames, Emails, Identifiers

**Rule:** Tool output alone never proves identity. Face verification (InsightFace) or multi-source corroboration required.

---

## Identifier states

| Status | Meaning |
|--------|---------|
| `CANDIDATE` | From Google, Sherlock, Holehe, SpiderFoot, or guess — **unverified** |
| `HARVESTED` | Playwright opened profile; screenshots saved |
| `VERIFIED` | Face match ≥ threshold OR (hypothesis mode) ≥2 independent public sources + face |
| `REJECTED` | Face mismatch, wrong person, or dead end |

Track in `{workspace}/identifiers_index.md`.

---

## Username verification flow

```
Sherlock / SpiderFoot / Google → username CANDIDATE
  → Playwright: open top 3 profile URLs (LinkedIn, IG, GitHub, etc.)
  → Screenshot if face visible
  → verify_accounts.py OR verify_identifier against reference.jpg
  → VERIFIED → may chain Holehe/SpiderFoot on linked email
  → REJECTED → remove from subject attribution; keep in tools log only
```

**Same username on Reddit + Instagram does NOT prove same person** until face or strong corroboration (e.g. same profile photo hash, cross-linked URLs in bio).

---

## Email verification flow

```
Holehe / Epieos / SpiderFoot → email CANDIDATE
  → Holehe: which platforms registered (no password reset)
  → Epieos (Playwright): Google account hints, avatar if any
  → If avatar: download/screenshot → face compare to reference
  → If no avatar: find public profile on registered platform → harvest face
  → VERIFIED only after face match OR email explicitly listed on VERIFIED LinkedIn
```

**Email on VERIFIED LinkedIn "contact info"** → auto-promote to VERIFIED (no face needed for the email string itself).

---

## When no reference face exists (Mode B)

1. Collect candidate names + faces from public sources (news, org sites, academic pages).
2. Store each person under `candidates/{slug}/` with `reference_candidate.jpg`.
3. Cross-link: org membership, co-authors, project names.
4. Promote to `subjects/` when evidence threshold met (document in `evidence_index.md`).
5. Optional: user provides reference later → re-run verify.

---

## What face verification does NOT do

- Prove criminal activity or org membership
- Geolocate live position
- Replace legal authorization for investigation

Face verify only answers: **"Does this public profile photo match this reference?"**
