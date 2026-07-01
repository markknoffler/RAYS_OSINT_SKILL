#!/usr/bin/env python3
"""Append structured investigation steps to workspace and project run logs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def log_step(
    *,
    workspace: Path | None,
    cwd: Path | None,
    phase: str,
    step: str,
    status: str,
    notes: str = "",
) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": ts,
        "phase": phase,
        "step": step,
        "status": status,
        "notes": notes,
        "workspace": str(workspace) if workspace else "",
    }

    if workspace:
        ws = workspace.resolve()
        ws.mkdir(parents=True, exist_ok=True)
        jsonl = ws / "run_steps.jsonl"
        with open(jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    if cwd:
        md_path = cwd.resolve() / "OSINT_RUN_LOG.md"
        line = f"- **{ts}** `[{status}]` **{phase}** — {step}"
        if notes:
            line += f"\n  - {notes}"
        if workspace:
            line += f"\n  - workspace: `{workspace}`"
        with open(md_path, "a", encoding="utf-8") as f:
            if md_path.stat().st_size == 0 or not md_path.exists():
                f.write("# OSINT Run Log\n\n")
            f.write(line + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Log an OSINT pipeline step")
    p.add_argument("--workspace", type=Path, default=None)
    p.add_argument("--cwd", type=Path, default=None)
    p.add_argument("--phase", required=True)
    p.add_argument("--step", required=True)
    p.add_argument("--status", required=True, choices=["ok", "fail", "blocked", "skipped", "partial"])
    p.add_argument("--notes", default="")
    args = p.parse_args()
    log_step(
        workspace=args.workspace,
        cwd=args.cwd,
        phase=args.phase,
        step=args.step,
        status=args.status,
        notes=args.notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
