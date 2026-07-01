#!/usr/bin/env python3
"""
Build and deduplicate network/social_graph.csv from raw follower/following lists.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.workspace import Workspace

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CSV_FIELDS = ["username", "relation", "profile_url", "display_name"]


def read_graph_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (row.get(k) or "").strip() for k in CSV_FIELDS})
    return rows


def write_graph_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        user = row.get("username", "").lower().lstrip("@")
        rel = row.get("relation", "").lower()
        if not user:
            continue
        key = (user, rel)
        if key in seen:
            continue
        seen.add(key)
        row["username"] = user
        out.append(row)
    return sorted(out, key=lambda r: (r.get("relation", ""), r.get("username", "")))


def build_graph(workspace: Path) -> int:
    ws = Workspace(workspace)
    ws.network_dir.mkdir(parents=True, exist_ok=True)

    raw_path = ws.social_graph_path
    rows = read_graph_csv(raw_path)
    if not rows:
        logger.warning(
            "No rows in %s — agent should populate CSV in Phase 6 first",
            raw_path,
        )
        write_graph_csv(raw_path, [])
        ws.append_log("build_social_graph: 0 rows (empty input)\n")
        return 0

    deduped = dedupe_rows(rows)
    write_graph_csv(raw_path, deduped)

    followers = sum(1 for r in deduped if r.get("relation") == "follower")
    following = sum(1 for r in deduped if r.get("relation") == "following")
    summary = (
        f"build_social_graph: total={len(deduped)} "
        f"followers={followers} following={following}\n"
    )
    ws.append_log(summary)
    print(summary.strip())

    # Ensure network/{username}/ dirs exist for metadata scraping
    for row in deduped:
        user = row.get("username", "")
        if user:
            (ws.network_dir / user).mkdir(parents=True, exist_ok=True)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dedupe and validate social_graph.csv")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    return build_graph(Path(args.workspace))


if __name__ == "__main__":
    raise SystemExit(main())
