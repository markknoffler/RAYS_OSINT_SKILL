#!/usr/bin/env python3
"""Initialize hypothesis-driven OSINT workspace (Mode B — no initial reference face)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:80] or "hypothesis"


def init_hypothesis_workspace(
    *,
    hypothesis_slug: str,
    cwd: Path,
    authorized_by: str,
    purpose: str,
    hypothesis_text: str,
) -> Path:
    workspace = (cwd / f"{hypothesis_slug}_osint").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    for sub in (
        "candidates",
        "subjects",
        "iterations",
        "tools/spiderfoot",
        "tools/sherlock",
        "tools/holehe",
        "articles",
        "network",
        "locations",
    ):
        (workspace / sub).mkdir(parents=True, exist_ok=True)

    hypothesis_md = workspace / "hypothesis.md"
    hypothesis_md.write_text(
        f"# Investigation Hypothesis\n\n"
        f"**Authorized by:** {authorized_by}\n"
        f"**Purpose:** {purpose}\n\n"
        f"## Hypothesis\n\n{hypothesis_text}\n\n"
        f"## Mode\n\nHypothesis-driven discovery (Mode B). See `docs/HYPOTHESIS_DISCOVERY_MODE.md`.\n",
        encoding="utf-8",
    )

    (workspace / "evidence_index.md").write_text(
        "# Evidence Index\n\n"
        "| person_slug | source_url | claim | confidence | status |\n"
        "| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )

    (workspace / "identifiers_index.md").write_text(
        "# Identifiers Index\n\n"
        "| type | value | source | verification_status | linked_profile |\n"
        "| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )

    (workspace / "scripts_log.txt").write_text(
        f"init_hypothesis_workspace: slug={hypothesis_slug}\n", encoding="utf-8"
    )
    return workspace


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hypothesis-slug", required=True)
    p.add_argument("--cwd", default=".", type=Path)
    p.add_argument("--authorized-by", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--hypothesis-text", required=True)
    args = p.parse_args()
    slug = slugify(args.hypothesis_slug)
    ws = init_hypothesis_workspace(
        hypothesis_slug=slug,
        cwd=args.cwd.resolve(),
        authorized_by=args.authorized_by,
        purpose=args.purpose,
        hypothesis_text=args.hypothesis_text,
    )
    print(str(ws))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
