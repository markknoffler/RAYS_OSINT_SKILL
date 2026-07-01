# Run Logging — Mandatory for Every Investigation

The agent **must** record every significant step so failures can be replayed and the skill improved.

---

## Files

| File | Location | Purpose |
|------|----------|---------|
| `OSINT_RUN_LOG.md` | User `--cwd` (project root) | Master chronological log across runs |
| `run_steps.jsonl` | Inside workspace | Machine-readable steps |
| `scripts_log.txt` | Inside workspace | Python script output (existing) |
| `iterations/iter_N.md` | Hypothesis mode only | Per-loop summary |

---

## Log every step

```bash
eval "$(bash scripts/resolve_paths.sh)"
$PYTHON $SKILL_SCRIPTS/log_step.py \
  --workspace "$WORKSPACE" \
  --cwd "$CWD" \
  --phase "1A-google" \
  --step "Plain Google search Samreedh Bhuyan" \
  --status ok \
  --notes "SERP loaded, 12 organic hits"
```

**Status values:** `ok`, `fail`, `blocked`, `skipped`, `partial`

**Phases:** `0-auth`, `0-tools`, `1A-google`, `1B-dorks`, `2-harvest`, `3-verify`, `T-sherlock`, `T-holehe`, `T-spiderfoot`, `T-epieos`, `10-relations`, `B-iter-N`, `8-report`

---

## After each investigation

1. Agent reads `{cwd}/OSINT_RUN_LOG.md`
2. Identify `fail` / `blocked` steps
3. Update SKILL.md or scripts if gap found
4. Re-run failed phase only

---

## Self-improvement loop (user requirement)

```
Run investigation → log steps → read log → patch skill/scripts → sync skill → re-run
```

Repeat until completion checklist passes or user stops.
