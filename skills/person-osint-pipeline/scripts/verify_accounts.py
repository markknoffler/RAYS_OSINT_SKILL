#!/usr/bin/env python3
"""
Pass 1: Verify account directories against reference face.
Deletes accounts with zero matching images; marks VERIFIED/REJECTED in accounts_index.md.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.face_engine import get_engine
from utils.workspace import STATUS_REJECTED, STATUS_VERIFIED, Workspace

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def verify_workspace(workspace: Path, reference: str | None, threshold: float) -> int:
    ws = Workspace(workspace)
    if not ws.root.exists():
        logger.error("Workspace not found: %s", workspace)
        return 1

    ref_path = ws.resolve_reference(reference)
    engine = get_engine()
    if not engine.load_reference(ref_path):
        return 1

    rows = ws.read_index_rows()
    if not rows:
        logger.warning("No rows in accounts_index.md — scanning account directories only")
        handle_dirs = [p.name for p in ws.account_dirs()]
    else:
        handle_dirs = [r.handle_dir for r in rows if r.handle_dir]

    verified_count = 0
    rejected_count = 0

    for handle in handle_dirs:
        account_path = ws.accounts_dir / handle
        if not account_path.is_dir():
            logger.warning("Missing account dir: %s", handle)
            ws.update_row_status(handle, STATUS_REJECTED)
            rejected_count += 1
            continue

        images = ws.images_in_account(account_path)
        if not images:
            logger.info("REJECT %s — no images", handle)
            ws.delete_account_dir(handle)
            ws.update_row_status(handle, STATUS_REJECTED)
            rejected_count += 1
            continue

        best_overall = -1.0
        for img in images:
            sim, n_faces = engine.score_image(img)
            if n_faces > 0:
                best_overall = max(best_overall, sim)
            logger.debug("  %s sim=%.3f faces=%d", img.name, sim, n_faces)

        if best_overall >= threshold:
            logger.info("VERIFY %s — best similarity %.3f", handle, best_overall)
            ws.update_row_status(handle, STATUS_VERIFIED)
            verified_count += 1
        else:
            logger.info(
                "REJECT %s — best similarity %.3f < threshold %.3f",
                handle,
                best_overall,
                threshold,
            )
            ws.delete_account_dir(handle)
            ws.update_row_status(handle, STATUS_REJECTED)
            rejected_count += 1

    summary = (
        f"verify_accounts: verified={verified_count} rejected={rejected_count} "
        f"threshold={threshold}\n"
    )
    ws.append_log(summary)
    print(summary.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OSINT account face matches")
    parser.add_argument("--workspace", required=True, help="Path to {subject}_osint/")
    parser.add_argument(
        "--reference",
        default=None,
        help="Reference image path (default: reference.jpg in workspace)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.45,
        help="Cosine similarity threshold (default: 0.45)",
    )
    args = parser.parse_args()
    return verify_workspace(Path(args.workspace), args.reference, args.threshold)


if __name__ == "__main__":
    raise SystemExit(main())
