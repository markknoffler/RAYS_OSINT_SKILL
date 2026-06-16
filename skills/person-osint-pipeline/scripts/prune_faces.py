#!/usr/bin/env python3
"""
Pass 2: Prune non-subject faces from verified account directories.
- Subject-matching images stay in account dir
- Other faces with detectable faces move to related/
- Images with no detectable face are deleted
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.face_engine import get_engine
from utils.workspace import STATUS_VERIFIED, Workspace

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def prune_workspace(
    workspace: Path,
    reference: str | None,
    match_threshold: float,
    face_threshold: float,
) -> int:
    ws = Workspace(workspace)
    ws.related_dir.mkdir(parents=True, exist_ok=True)

    ref_path = ws.resolve_reference(reference)
    engine = get_engine()
    if not engine.load_reference(ref_path):
        return 1

    rows = ws.read_index_rows()
    verified_handles = {
        r.handle_dir for r in rows if r.verification_status == STATUS_VERIFIED
    }
    if not verified_handles:
        verified_handles = {p.name for p in ws.account_dirs()}

    related_hashes: set[str] = set()
    moved = 0
    kept = 0
    deleted = 0

    for handle in sorted(verified_handles):
        account_path = ws.accounts_dir / handle
        if not account_path.is_dir():
            continue

        for img in ws.images_in_account(account_path):
            sim, n_faces = engine.score_image(img)

            if n_faces == 0:
                logger.info("DELETE %s/%s — no face", handle, img.name)
                img.unlink()
                deleted += 1
                continue

            if sim >= match_threshold:
                logger.info("KEEP %s/%s sim=%.3f", handle, img.name, sim)
                kept += 1
                continue

            # Face present but not subject — move to related/
            h = _content_hash(img)
            if h in related_hashes:
                img.unlink()
                deleted += 1
                continue

            dest_name = f"{handle}_{img.stem}.png"
            dest = ws.related_dir / dest_name
            if dest.exists():
                dest = ws.related_dir / f"{handle}_{img.stem}_{h}.png"

            shutil.move(str(img), str(dest))
            related_hashes.add(h)
            moved += 1
            logger.info("RELATED %s -> %s (sim=%.3f)", img.name, dest.name, sim)

    summary = (
        f"prune_faces: kept={kept} moved_to_related={moved} deleted={deleted} "
        f"match_threshold={match_threshold}\n"
    )
    ws.append_log(summary)
    print(summary.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune non-subject faces to related/")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--reference", default=None)
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.45,
        help="Similarity to keep image in account dir",
    )
    parser.add_argument(
        "--face-threshold",
        type=float,
        default=0.0,
        help="Reserved for future use",
    )
    args = parser.parse_args()
    return prune_workspace(
        Path(args.workspace),
        args.reference,
        args.match_threshold,
        args.face_threshold,
    )


if __name__ == "__main__":
    raise SystemExit(main())
