#!/usr/bin/env python
"""Scan a drive and ingest results into DuckDB using the manifest.

Usage:
  python scripts/scan_and_ingest.py --drive Ext-10 [--db catalogue.duckdb] [--manifest drive_manifest.csv] [--outdir output]

Behavior:
  - Looks up the drive in the manifest (by drive_label).
  - Resolves the container path (prefers mac path under /host/Volumes).
  - Skips scan/ingest if the drive already has rows in any target table, unless --force.
  - Runs three scans (files, photos, videos) and then ingests from the drive-specific output folder.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import duckdb
import csv as _csv
from datetime import datetime


@dataclass
class ManifestEntry:
    drive_label: str
    mac_mount: Optional[str]


def load_manifest(manifest_path: Path) -> dict[str, ManifestEntry]:
    entries: dict[str, ManifestEntry] = {}
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("drive_label") or "").strip()
            platform = (row.get("platform_mount") or "").strip()
            mac_mount: Optional[str] = None
            # Parse a token like: "mac:/Volumes/Ext-10 | win:E:\\"
            for token in platform.split("|"):
                token = token.strip()
                if token.lower().startswith("mac:"):
                    mac_mount = token.split(":", 1)[1].strip()
                    break
            if label:
                entries[label] = ManifestEntry(drive_label=label, mac_mount=mac_mount)
    return entries


def to_container_path(mac_path: str) -> str:
    # Map host mac path /Volumes/... to container /host/Volumes/...
    if mac_path.startswith("/Volumes/"):
        return mac_path.replace("/Volumes/", "/host/Volumes/", 1)
    return mac_path


def table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    q = """
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'main' AND table_name = ? LIMIT 1
    """
    return con.execute(q, [table]).fetchone() is not None


def has_rows_for_drive(con: duckdb.DuckDBPyConnection, table: str, drive_label: str) -> bool:
    if not table_exists(con, table):
        return False
    q = (
        "SELECT 1 FROM "
        + table
        + " WHERE regexp_extract(SourceFile, '/host/Volumes/([^/]+)/', 1) = ? LIMIT 1"
    )
    return con.execute(q, [drive_label]).fetchone() is not None


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def latest_csv(outdir_drive: Path, prefix: str) -> Optional[Path]:
    candidates = sorted(outdir_drive.glob(f"{prefix}*.csv"))
    return candidates[-1] if candidates else None


PHOTO_EXT = {
    "arw", "arq", "srx", "sr2", "cr2", "raf", "nef", "dng",
    "jpg", "jpeg", "tiff", "tif", "png", "heic", "heif",
}
VIDEO_EXT = {
    "mp4", "mov", "mxf", "avi", "mpg", "mpeg", "mts", "mkv",
}


def derive_lists_from_files_csv(files_csv: Path, outdir_drive: Path) -> tuple[Path, Path]:
    photos_list = outdir_drive / "photos_list.txt"
    videos_list = outdir_drive / "videos_list.txt"
    with files_csv.open(newline="", encoding="utf-8") as f, \
            photos_list.open("w", encoding="utf-8") as fp, \
            videos_list.open("w", encoding="utf-8") as fv:
        reader = _csv.DictReader(f)
        for row in reader:
            src = (row.get("SourceFile") or row.get("SourceFile") or "").strip()
            if not src:
                continue
            ext = Path(src).suffix.lower().lstrip(".")
            if ext in PHOTO_EXT:
                fp.write(src + "\n")
            elif ext in VIDEO_EXT:
                fv.write(src + "\n")
    return photos_list, videos_list


def count_csv_rows(p: Optional[Path]) -> int:
    if not p or not p.exists():
        return 0
    try:
        with p.open("r", encoding="utf-8", newline="") as f:
            # Subtract one for header
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


def ensure_drive_scans_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS drive_scans (
          drive_label TEXT,
          started_at TIMESTAMP,
          ended_at TIMESTAMP,
          status TEXT,
          files_csv TEXT,
          photos_csv TEXT,
          videos_csv TEXT,
          files_rows BIGINT,
          photos_rows BIGINT,
          videos_rows BIGINT
        );
        """
    )


def insert_drive_scan(
    con: duckdb.DuckDBPyConnection,
    drive_label: str,
    started_at: datetime,
    ended_at: datetime,
    status: str,
    files_csv: Optional[Path],
    photos_csv: Optional[Path],
    videos_csv: Optional[Path],
) -> None:
    ensure_drive_scans_table(con)
    con.execute(
        """
        INSERT INTO drive_scans(
          drive_label, started_at, ended_at, status,
          files_csv, photos_csv, videos_csv,
          files_rows, photos_rows, videos_rows
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        [
            drive_label,
            started_at,
            ended_at,
            status,
            str(files_csv) if files_csv else None,
            str(photos_csv) if photos_csv else None,
            str(videos_csv) if videos_csv else None,
            count_csv_rows(files_csv),
            count_csv_rows(photos_csv),
            count_csv_rows(videos_csv),
        ],
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive", required=True, help="Drive label in manifest (e.g., Ext-10)")
    ap.add_argument("--db", default="catalogue.duckdb", help="DuckDB database path")
    ap.add_argument(
        "--manifest", default="drive_manifest.csv", help="Path to drive manifest CSV"
    )
    ap.add_argument("--outdir", default="output", help="Base output directory for CSVs")
    ap.add_argument("--update-manifest", action="store_true", help="If drive is missing from manifest, attempt to update it by scanning mounted volumes")
    ap.add_argument("--prefix", default="", help="Optional label prefix when auto-updating the manifest")
    ap.add_argument("--force", action="store_true", help="Force re-scan even if indexed")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    start_time = datetime.now()
    if not manifest_path.exists():
        raise SystemExit(
            f"Manifest not found: {manifest_path}. Copy drive_manifest.template.csv to drive_manifest.csv and fill your drive details."
        )

    def load_entry() -> Optional[ManifestEntry]:
        entries = load_manifest(manifest_path)
        return entries.get(args.drive)

    entry = load_entry()
    if not entry:
        if args.update_manifest:
            print(f"Drive label '{args.drive}' not found in manifest. Attempting to update manifest...")
            # Try to add current volumes to the manifest
            run([
                "python",
                "scripts/make_manifest.py",
                "--manifest",
                str(manifest_path),
                "--prefix",
                args.prefix,
            ])
            entry = load_entry()
        if not entry:
            raise SystemExit(
                f"Drive label not found in manifest: {args.drive}.\n"
                f"- Edit {manifest_path} to add it,\n"
                f"- or run: python scripts/make_manifest.py --manifest {manifest_path} [--prefix PREFIX],\n"
                f"- or re-run this command with --update-manifest."
            )

    # Resolve container path
    if entry.mac_mount:
        drive_path = to_container_path(entry.mac_mount)
    else:
        drive_path = f"/host/Volumes/{args.drive}"

    drive_path_p = Path(drive_path)
    if not drive_path_p.exists():
        raise SystemExit(f"Drive path not found or not mounted in container: {drive_path}")

    # Decide per-table whether to scan
    con = duckdb.connect(args.db)
    need_files = not has_rows_for_drive(con, "files_raw", args.drive)
    need_photos = not has_rows_for_drive(con, "photos_raw", args.drive)
    need_videos = not has_rows_for_drive(con, "videos_raw", args.drive)
    if args.force:
        need_files = need_photos = need_videos = True
    # Close DB before running child processes that will also open it (avoids file lock)
    con.close()

    # Prepare output dir per drive
    outdir_drive = Path(args.outdir) / args.drive
    outdir_drive.mkdir(parents=True, exist_ok=True)

    # Run needed scans
    if not (need_files or need_photos or need_videos):
        print(
            f"Drive '{args.drive}' already indexed in files/photos/videos. Skipping scans; recording drive snapshot."
        )
        # Record/update drive metadata snapshot in DB even if no scans are needed
        con = duckdb.connect(args.db)
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS drives (
              drive_label TEXT PRIMARY KEY,
              mac_mount TEXT,
              volume_uuid TEXT,
              serial_number TEXT,
              notes TEXT,
              last_scanned TIMESTAMP
            );
            """
        )
        # Reload full manifest row
        with open(args.manifest, newline="", encoding="utf-8") as mf:
            r = _csv.DictReader(mf)
            vol_uuid = serial = notes = None
            plat = None
            for row in r:
                if (row.get("drive_label") or "").strip() == args.drive:
                    plat = (row.get("platform_mount") or "").strip() or None
                    vol_uuid = (row.get("volume_uuid") or "").strip() or None
                    serial = (row.get("serial_number") or "").strip() or None
                    notes = (row.get("notes") or "").strip() or None
                    break
        con.execute("DELETE FROM drives WHERE drive_label = ?", [args.drive])
        con.execute(
            "INSERT INTO drives(drive_label, mac_mount, volume_uuid, serial_number, notes, last_scanned) VALUES (?,?,?,?,?,?)",
            [args.drive, plat or entry.mac_mount, vol_uuid, serial, notes, datetime.now()],
        )
        # Also record a drive_scans history record with status 'skipped'
        try:
            insert_drive_scan(
                con,
                args.drive,
                started_at=start_time,
                ended_at=datetime.now(),
                status="skipped",
                files_csv=None,
                photos_csv=None,
                videos_csv=None,
            )
        finally:
            con.close()
        print(f"Drive '{args.drive}' snapshot recorded.")
        return
    files_csv: Optional[Path] = None
    if need_files:
        run(["./scripts/container_scan_files.sh", drive_path, args.drive, str(outdir_drive)])
        files_csv = latest_csv(outdir_drive, "files_")
    else:
        files_csv = latest_csv(outdir_drive, "files_")

    # If we have a files CSV, derive targeted lists for efficient media extraction
    photo_list_path: Optional[Path] = None
    video_list_path: Optional[Path] = None
    if files_csv and (need_photos or need_videos):
        photo_list_path, video_list_path = derive_lists_from_files_csv(files_csv, outdir_drive)

    if need_photos:
        if photo_list_path and photo_list_path.exists():
            run(["./scripts/container_extract_photos_from_list.sh", str(photo_list_path), args.drive, str(outdir_drive)])
        else:
            run(["./scripts/container_scan_photos.sh", drive_path, args.drive, str(outdir_drive)])
    if need_videos:
        if video_list_path and video_list_path.exists():
            run(["./scripts/container_extract_videos_from_list.sh", str(video_list_path), args.drive, str(outdir_drive)])
        else:
            run(["./scripts/container_scan_videos.sh", drive_path, args.drive, str(outdir_drive)])

    # Ingest
    run([
        "python",
        "scripts/load_csvs.py",
        "--db",
        args.db,
        "--dir",
        str(outdir_drive),
    ])

    # Record/update drive metadata snapshot in DB and write drive_scans history
    con = duckdb.connect(args.db)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS drives (
          drive_label TEXT PRIMARY KEY,
          mac_mount TEXT,
          volume_uuid TEXT,
          serial_number TEXT,
          notes TEXT,
          last_scanned TIMESTAMP
        );
        """
    )
    mac_mount = entry.mac_mount or None
    # We also store raw platform_mount string for reference if present
    # Extract other fields directly from manifest if available
    # Reload row from manifest to get all columns
    with open(args.manifest, newline="", encoding="utf-8") as mf:
        r = _csv.DictReader(mf)
        vol_uuid = serial = notes = None
        plat = None
        for row in r:
            if (row.get("drive_label") or "").strip() == args.drive:
                plat = (row.get("platform_mount") or "").strip() or None
                vol_uuid = (row.get("volume_uuid") or "").strip() or None
                serial = (row.get("serial_number") or "").strip() or None
                notes = (row.get("notes") or "").strip() or None
                break
    # Upsert by delete+insert to avoid ON CONFLICT dependency
    con.execute("DELETE FROM drives WHERE drive_label = ?", [args.drive])
    con.execute(
        "INSERT INTO drives(drive_label, mac_mount, volume_uuid, serial_number, notes, last_scanned) VALUES (?,?,?,?,?,?)",
        [args.drive, plat or mac_mount, vol_uuid, serial, notes, datetime.now()],
    )
    # Determine latest CSVs used in this run
    files_csv = latest_csv(outdir_drive, "files_")
    photos_csv = latest_csv(outdir_drive, "photos_")
    videos_csv = latest_csv(outdir_drive, "videos_")
    insert_drive_scan(
        con,
        args.drive,
        started_at=start_time,
        ended_at=datetime.now(),
        status="ok",
        files_csv=files_csv,
        photos_csv=photos_csv,
        videos_csv=videos_csv,
    )
    con.close()

    print(f"Drive '{args.drive}' scan + ingest complete.")


if __name__ == "__main__":  # pragma: no cover
    main()
