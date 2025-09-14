#!/usr/bin/env python3
from __future__ import annotations

"""Generate a markdown schema reference for the catalogue DuckDB.

Usage:
  python scripts/generate_schema_reference.py --db catalogue.duckdb --out SCHEMA_REFERENCE.md

The script inspects tables and views in the DuckDB database and writes a
reference markdown file listing columns, types, and brief descriptions.
Known/derived columns receive explicit descriptions; other columns from the
ExifTool CSVs are labeled as raw ExifTool fields.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb


@dataclass
class Column:
    name: str
    typ: str
    desc: str


KNOWN_COLUMN_DESCRIPTIONS: dict[str, str] = {
    # Canonical/derived columns in views
    "Drive": "Volume label parsed from SourceFile (/host/Volumes/<Drive>/...).",
    "RelativePath": "Path within the drive root (SourceFile without the /host/Volumes/<Drive>/ prefix).",
    "RelativeDirectory": "Directory component of RelativePath (no leading slash).",
    "FileExt": "Lowercased file extension without the dot.",
    "FileKey": "Stable per-file identifier: hash(Drive, RelativePath, FileSize#).",
    # Common ExifTool fields (subset — others will be tagged as raw ExifTool)
    "SourceFile": "Absolute path to the scanned file (container path if inside devcontainer).",
    "Directory": "Directory portion of the SourceFile path.",
    "FileName": "Base name of the file including extension.",
    "FileSize#": "File size in bytes (numeric).",
    "MIMEType": "Detected MIME type of the file.",
    "Model": "Camera model (for photos/videos when available).",
    "Make": "Camera manufacturer (when available).",
    "LensModel": "Lens model (when available).",
    "LensID": "Lens identifier (when available).",
    "FNumber": "Aperture (f-stop).",
    "ShutterSpeed": "Exposure time / shutter speed.",
    "ISO": "ISO sensitivity.",
    "FocalLength": "Focal length.",
    "ImageWidth": "Pixel width of the image or video frame.",
    "ImageHeight": "Pixel height of the image or video frame.",
    "Orientation": "Image orientation metadata.",
    "GPSLatitude": "Latitude in decimal degrees (if GPS present).",
    "GPSLongitude": "Longitude in decimal degrees (if GPS present).",
    "Rating": "User rating (if embedded).",
    "Label": "User label/flag (if embedded).",
    "XMP-dc:Title": "XMP title field (if embedded).",
    "Keywords": "Flat keywords list (if embedded).",
    "HierarchicalSubject": "Hierarchical keywords (if embedded).",
    "DateTimeOriginal": "Original capture timestamp (photos).",
    "CreateDate": "File or media creation timestamp.",
    "ModifyDate": "Last modification timestamp.",
    "Duration": "Media duration (videos).",
    "TrackCreateDate": "Track creation timestamp (videos).",
    "MediaCreateDate": "Media create timestamp (videos).",
    "HandlerDescription": "Media handler description (videos).",
    "CompressorName": "Compressor/codec name (videos).",
    "VideoCodec": "Video codec (videos).",
    "VideoFrameRate": "Video frame rate (videos).",
    "VideoFrameCount": "Number of frames (videos).",
    "AudioFormat": "Audio format (videos).",
    "AudioChannels": "Audio channel count (videos).",
    "AudioSampleRate": "Audio sample rate (videos).",
    "BitRate": "Overall bit rate (videos).",
}


OBJECT_PURPOSE: dict[str, str] = {
    # Base/raw tables from CSVs
    "files_raw": "Raw ExifTool scan of all files; columns mirror CSV headers.",
    "photos_raw": "Raw ExifTool scan for photo files; columns mirror CSV headers.",
    "videos_raw": "Raw ExifTool scan for video files; columns mirror CSV headers.",
    # Derived convenience views
    "files": "All files with derived identifiers and drive/path parsing.",
    "photos": "Photos with derived identifiers and drive/path parsing.",
    "videos": "Videos with derived identifiers and drive/path parsing.",
    # Operational tables
    "ingested_files": "Ingestion log of CSVs already loaded (idempotency).",
    "drives": "Drive metadata snapshot from manifest (label, mounts, ids, notes).",
    "drive_scans": "History of scan runs per drive (start/end, status, CSVs, row counts).",
}


def list_objects(con: duckdb.DuckDBPyConnection) -> tuple[list[str], list[str]]:
    rows = con.sql(
        "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    tables = [r[0] for r in rows if r[1] == "BASE TABLE"]
    views = [r[0] for r in rows if r[1] == "VIEW"]
    return sorted(tables), sorted(views)


def describe_table(con: duckdb.DuckDBPyConnection, name: str) -> list[Column]:
    # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
    cols = con.sql(f"PRAGMA table_info('{name}')").fetchall()
    return [
        Column(
            name=c[1],
            typ=str(c[2]),
            desc=KNOWN_COLUMN_DESCRIPTIONS.get(c[1], "Raw ExifTool field or operational field."),
        )
        for c in cols
    ]


def describe_view(con: duckdb.DuckDBPyConnection, name: str) -> list[Column]:
    # DESCRIBE view: column_name, column_type, null, key, default, extra
    cols = con.sql(f"DESCRIBE {name}").fetchall()
    result: list[Column] = []
    for c in cols:
        col_name = str(c[0])
        col_type = str(c[1])
        # Prefer UBIGINT for FileKey when DuckDB reports BIGINT
        if col_name == "FileKey" and col_type.upper() == "BIGINT":
            col_type = "UBIGINT"
        result.append(
            Column(
                name=col_name,
                typ=col_type,
                desc=KNOWN_COLUMN_DESCRIPTIONS.get(col_name, "Raw ExifTool field or derived column."),
            )
        )
    return result


def md_header(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n\n"


def md_bullets(items: Iterable[str]) -> str:
    return "".join(f"- {i}\n" for i in items) + "\n"


def md_table(columns: list[Column]) -> str:
    lines = ["| Column | Type | Description |", "|---|---|---|"]
    for c in columns:
        # Escape pipes in description
        desc = c.desc.replace("|", "\\|")
        lines.append(f"| `{c.name}` | `{c.typ}` | {desc} |")
    return "\n".join(lines) + "\n\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate schema reference markdown from DuckDB")
    ap.add_argument("--db", default="catalogue.duckdb", help="DuckDB database path")
    ap.add_argument("--out", default="SCHEMA_REFERENCE.md", help="Output markdown path")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    con = duckdb.connect(str(db_path))
    tables, views = list_objects(con)

    # Order objects: operational tables, raw tables, derived views
    preferred_order = [
        "drives",
        "drive_scans",
        "ingested_files",
        "files_raw",
        "photos_raw",
        "videos_raw",
        "files",
        "photos",
        "videos",
    ]

    def sort_objects(names: list[str]) -> list[str]:
        rank = {name: i for i, name in enumerate(preferred_order)}
        return sorted(names, key=lambda n: (rank.get(n, 10_000), n))

    tables = sort_objects(tables)
    views = sort_objects(views)

    out = []
    out.append(md_header(1, "Disk Catalogue Schema Reference"))
    out.append(
        "This document describes the tables and views in the DuckDB catalogue, "
        "including column types and brief explanations. Columns not explicitly described "
        "are carried through from the ExifTool CSV outputs."
        "\n\n"
    )

    out.append(md_header(2, "How It’s Built"))
    out.append(md_bullets(
        [
            "Raw CSVs from scans load into *_raw tables (schema auto‑detected).",
            "Views (files/photos/videos) add derived identifiers: Drive, RelativePath, RelativeDirectory, FileExt, FileKey.",
            "Operational tables track ingests and scans: ingested_files, drives, drive_scans.",
        ]
    ))

    # Tables
    out.append(md_header(2, "Tables"))
    for t in tables:
        purpose = OBJECT_PURPOSE.get(t, "Base table.")
        out.append(md_header(3, t))
        out.append(purpose + "\n\n")
        cols = describe_table(con, t)
        out.append(md_table(cols))

    # Views
    out.append(md_header(2, "Views"))
    for v in views:
        purpose = OBJECT_PURPOSE.get(v, "View.")
        out.append(md_header(3, v))
        out.append(purpose + "\n\n")
        cols = describe_view(con, v)
        out.append(md_table(cols))

    Path(args.out).write_text("".join(out), encoding="utf-8")
    print(f"Wrote schema reference to {args.out}")


if __name__ == "__main__":  # pragma: no cover
    main()
