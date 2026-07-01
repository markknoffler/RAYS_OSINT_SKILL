# Mode B — Hypothesis-Driven Discovery (no initial name/face)

Use when the user gives a **hypothesis** instead of a person:

> "Find nuclear scientists linked to Taliban-affiliated programs that may threaten world peace."

---

## Phase 0 — Authorization (stricter)

Required fields:

- `authorized_by` — organization or individual with legitimate purpose
- `purpose` — threat intelligence, academic research, journalism, etc.
- `scope` — countries, orgs, time range
- **Refuse** vague harassment, doxing, or unauthorized surveillance

Record in `hypothesis.md`.

---

## Workspace init

```bash
python scripts/init_hypothesis_workspace.py \
  --hypothesis-slug taliban_nuclear_threat \
  --cwd /path/to/project \
  --authorized-by "..." \
  --purpose "Threat intelligence research" \
  --hypothesis-text "Nuclear scientists with Taliban-linked programs"
```

Creates `{hypothesis_slug}_osint/` with:

- `hypothesis.md`, `candidates/`, `subjects/`, `evidence_index.md`
- No `reference.jpg` until a candidate face is isolated

---

## Iterative discovery loop (agent-driven)

Repeat until stop condition or user cap:

```
1. Google (plain + dorks from hypothesis)
   e.g. "Afghanistan nuclear scientist", "Taliban nuclear", site:edu nuclear Pakistan
2. Open EACH SERP hit → extract names, orgs, faces, papers
3. For each named person with photo:
   - Save to candidates/{slug}/profile.png
   - Write evidence_index row (source URL, claim, confidence)
4. Run SpiderFoot on org domains / emails found (passive)
5. Run Sherlock on usernames discovered
6. Filter: remove candidates contradicted by sources
7. Cross-verify remaining: co-author graphs, org affiliation, dated news
8. If reference face obtained → verify_accounts on candidate dirs
9. Re-Google with newly learned names/orgs (expanded query set)
10. Write iteration summary to iterations/iter_N.md
```

**Stop when:** user limit reached, no new candidates in 2 iterations, or sufficient subjects documented with evidence.

---

## Evidence standards (public OSINT)

| Level | Criteria |
|-------|----------|
| LOW | Name match only, no org link |
| MEDIUM | Named in credible news/academic source + org |
| HIGH | Multiple independent sources + photo + role description |
| VERIFIED_SUBJECT | HIGH + face consistent across ≥2 photos OR user-supplied reference match |

Never claim "terrorist" or "threat" without cited public sources in `evidence_index.md`.

---

## Relationship mapping (Phase 10)

For each HIGH+ candidate:

- Co-authors, colleagues, org chart from LinkedIn/academic pages
- `network/org_graph.csv`: person_a, person_b, relation, source_url
- SpiderFoot on institutional domains

---

## Limitations (document in final_report.md)

- Open OSINT rarely yields classified program details
- Many results will be unrelated homonyms
- Geolocation precision requires image forensics (Overpass/VLM), not live tracking
- Pipeline finds **publicly documentable leads**, not covert identities
