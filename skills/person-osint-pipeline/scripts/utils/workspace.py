"""Workspace paths, manifest parsing, and safe directory operations."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .image_naming import PROFILE_FILENAME, is_image_file

STATUS_CANDIDATE = "CANDIDATE"
STATUS_HARVESTED = "HARVESTED"
STATUS_VERIFIED = "VERIFIED"
STATUS_REJECTED = "REJECTED"

TABLE_HEADER = (
    "| platform | profile_url | handle_dir | verification_status | image_links |"
)
TABLE_SEP = "| --- | --- | --- | --- | --- |"


@dataclass
class AccountRow:
    platform: str
    profile_url: str
    handle_dir: str
    verification_status: str
    image_links: list[str] = field(default_factory=list)

    def to_md_row(self) -> str:
        links = "; ".join(self.image_links) if self.image_links else "—"
        return (
            f"| {self.platform} | {self.profile_url} | {self.handle_dir} | "
            f"{self.verification_status} | {links} |"
        )


class Workspace:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.accounts_dir = self.root / "accounts"
        self.related_dir = self.root / "related"
        self.locations_dir = self.root / "locations"
        self.network_dir = self.root / "network"
        self.index_path = self.root / "accounts_index.md"
        self.log_path = self.root / "scripts_log.txt"
        self.reference_path = self.root / "reference.jpg"
        self.final_report_path = self.root / "final_report.md"
        self.social_graph_path = self.network_dir / "social_graph.csv"

    def ensure_layout(self) -> None:
        for d in (
            self.accounts_dir,
            self.related_dir,
            self.locations_dir,
            self.network_dir,
            self.root / "tools" / "spiderfoot",
            self.root / "tools" / "sherlock",
            self.root / "tools" / "holehe",
            self.root / "tools" / "epieos",
        ):
            d.mkdir(parents=True, exist_ok=True)

    def append_log(self, text: str) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")

    def read_index_rows(self) -> list[AccountRow]:
        if not self.index_path.exists():
            return []
        text = self.index_path.read_text(encoding="utf-8")
        rows: list[AccountRow] = []
        in_table = False
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("| platform"):
                in_table = True
                continue
            if in_table and line.startswith("| ---"):
                continue
            if in_table and line.startswith("|"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) < 5:
                    continue
                links_raw = parts[4]
                links = (
                    [x.strip() for x in links_raw.split(";") if x.strip() and x != "—"]
                    if links_raw and links_raw != "—"
                    else []
                )
                rows.append(
                    AccountRow(
                        platform=parts[0],
                        profile_url=parts[1],
                        handle_dir=parts[2],
                        verification_status=parts[3],
                        image_links=links,
                    )
                )
            elif in_table and not line.startswith("|"):
                break
        return rows

    def write_index_rows(
        self,
        rows: list[AccountRow],
        header_meta: dict[str, str] | None = None,
    ) -> None:
        meta = header_meta or self._read_header_meta()
        lines = [
            "# Accounts Index",
            "",
            f"**Subject workspace:** `{self.root}`",
            "",
        ]
        if meta.get("authorized_by"):
            lines.append(f"**Authorized by:** {meta['authorized_by']}")
        if meta.get("purpose"):
            lines.append(f"**Purpose:** {meta['purpose']}")
        if meta.get("subject_name"):
            lines.append(f"**Subject:** {meta['subject_name']}")
        lines.extend(["", "## Accounts", "", TABLE_HEADER, TABLE_SEP])
        for row in rows:
            lines.append(row.to_md_row())
        lines.append("")
        self.index_path.write_text("\n".join(lines), encoding="utf-8")

    def _read_header_meta(self) -> dict[str, str]:
        if not self.index_path.exists():
            return {}
        meta: dict[str, str] = {}
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\*\*Authorized by:\*\*\s*(.+)", line)
            if m:
                meta["authorized_by"] = m.group(1).strip()
            m = re.match(r"\*\*Purpose:\*\*\s*(.+)", line)
            if m:
                meta["purpose"] = m.group(1).strip()
            m = re.match(r"\*\*Subject:\*\*\s*(.+)", line)
            if m:
                meta["subject_name"] = m.group(1).strip()
        return meta

    def update_row_status(self, handle_dir: str, status: str) -> None:
        rows = self.read_index_rows()
        for row in rows:
            if row.handle_dir == handle_dir:
                row.verification_status = status
        self.write_index_rows(rows)

    def account_dirs(self) -> Iterator[Path]:
        if not self.accounts_dir.exists():
            return
        for p in sorted(self.accounts_dir.iterdir()):
            if p.is_dir():
                yield p

    def images_in_account(self, account_dir: Path) -> list[Path]:
        return sorted(
            f for f in account_dir.iterdir() if f.is_file() and is_image_file(f)
        )

    def delete_account_dir(self, handle_dir: str) -> None:
        path = self.accounts_dir / handle_dir
        if path.exists():
            shutil.rmtree(path)

    def resolve_reference(self, reference_arg: str | None) -> Path:
        if reference_arg:
            p = Path(reference_arg)
            if not p.is_absolute():
                p = self.root / p
            if p.exists():
                return p.resolve()
        for name in ("reference.jpg", "reference.jpeg", "reference.png"):
            p = self.root / name
            if p.exists():
                return p.resolve()
        raise FileNotFoundError(
            f"No reference image found in {self.root} (tried reference.jpg/png)"
        )
