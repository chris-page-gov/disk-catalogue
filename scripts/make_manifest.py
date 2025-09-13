#!/usr/bin/env python
"""Bootstrap or update the local drive manifest from currently mounted volumes.

Usage:
  python scripts/make_manifest.py [--manifest drive_manifest.csv] [--prefix PREFIX]

Behavior:
  - Enumerates folders under /host/Volumes (Dev Container binding of macOS /Volumes).
  - Creates `drive_manifest.csv` if missing (using the repository header structure).
  - Appends rows for volumes not already present, using:
      drive_label = f"{PREFIX}{volume_name}" (default PREFIX is empty)
      platform_mount = f"mac:/Volumes/{volume_name}"
      volume_uuid, serial_number, notes = empty
  - Does not overwrite or remove existing rows.

Note: The manifest is gitignored; commit `drive_manifest.template.csv` only.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


HEADER = ["drive_label", "platform_mount", "volume_uuid", "serial_number", "notes"]


def list_host_volumes(root: Path = Path("/host/Volumes")) -> Iterable[str]:
    if not root.exists():
        return []
    for entry in sorted(root.iterdir()):
        try:
            if entry.is_dir():
                yield entry.name
        except OSError:
            continue


def read_existing_labels(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    with manifest.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return { (row.get("drive_label") or "").strip() for row in reader }


def ensure_header(manifest: Path) -> None:
    if manifest.exists() and manifest.stat().st_size > 0:
        return
    # Create new manifest with header
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)


def append_rows(manifest: Path, rows: list[list[str]]) -> None:
    with manifest.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="drive_manifest.csv", help="Path to manifest CSV")
    ap.add_argument("--prefix", default="", help="Optional label prefix for generated drive labels")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    ensure_header(manifest)

    existing = read_existing_labels(manifest)
    new_rows: list[list[str]] = []
    for name in list_host_volumes():
        label = f"{args.prefix}{name}"
        if label in existing:
            continue
        platform = f"mac:/Volumes/{name}"
        new_rows.append([label, platform, "", "", ""])

    if not new_rows:
        print("No new volumes to add. Manifest unchanged.")
        return

    append_rows(manifest, new_rows)
    print(f"Added {len(new_rows)} volume(s) to {manifest}:")
    for r in new_rows:
        print(f" - {r[0]} -> {r[1]}")


if __name__ == "__main__":  # pragma: no cover
    main()

