#!/usr/bin/env python3
"""Initialize an OSINT investigation workspace in the user's CWD."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"

sys.path.insert(0, str(SCRIPT_DIR))

from utils.image_naming import workspace_dir_name
from utils.workspace import Workspace


def _render_template(name: str, **kwargs: str) -> str:
    path = TEMPLATE_DIR / name
    text = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace("{" + key + "}", value)
    return text


def init_workspace(
    *,
    subject_name: str,
    reference_photo: Path,
    cwd: Path,
    authorized_by: str,
    purpose: str,
) -> Path:
    workspace_name = workspace_dir_name(subject_name)
    workspace = (cwd / workspace_name).resolve()
    ws = Workspace(workspace)
    ws.ensure_layout()

    ref_src = reference_photo.resolve()
    if not ref_src.is_file():
        raise FileNotFoundError(f"Reference photo not found: {ref_src}")

    ref_dest = ws.reference_path
    if ref_src.suffix.lower() in {".jpg", ".jpeg"}:
        shutil.copy2(ref_src, ref_dest)
    else:
        from PIL import Image

        img = Image.open(ref_src)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(ref_dest, format="JPEG", quality=95)

    # Validate reference contains a detectable face before proceeding
    from utils.face_engine import get_engine

    engine = get_engine()
    if not engine._detect(ref_dest):
        raise ValueError(
            f"No face detected in reference photo: {ref_src}. "
            "Provide a clear frontal portrait (not a full-page screenshot)."
        )

    index_text = _render_template(
        "accounts_index.md.tpl",
        workspace_path=str(workspace),
        subject_name=subject_name,
        authorized_by=authorized_by,
        purpose=purpose,
    )
    ws.index_path.write_text(index_text, encoding="utf-8")
    id_tpl = TEMPLATE_DIR / "identifiers_index.md.tpl"
    if id_tpl.is_file():
        shutil.copy2(id_tpl, workspace / "identifiers_index.md")
    ws.append_log(
        f"init_workspace: subject={subject_name!r} reference={ref_dest.name}\n"
    )
    return workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize person OSINT workspace")
    parser.add_argument("--subject-name", required=True)
    parser.add_argument("--reference-photo", required=True, type=Path)
    parser.add_argument("--cwd", default=".", type=Path)
    parser.add_argument("--authorized-by", required=True)
    parser.add_argument("--purpose", required=True)
    args = parser.parse_args()

    workspace = init_workspace(
        subject_name=args.subject_name,
        reference_photo=args.reference_photo,
        cwd=args.cwd.resolve(),
        authorized_by=args.authorized_by,
        purpose=args.purpose,
    )
    print(str(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
