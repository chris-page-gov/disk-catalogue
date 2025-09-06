#!/usr/bin/env python
"""Load latest scan CSVs into DuckDB tables.

Usage:
  python scripts/load_csvs.py [--db catalogue.duckdb] [--dir output]

Behavior:
  - Creates tables if they do not exist (photos_raw, videos_raw).
  - Loads all matching CSVs (photos_*.csv, videos_*.csv) incrementally.
  - Skips files already recorded in an ingestion log table.
"""
from __future__ import annotations

import argparse
import duckdb
from pathlib import Path

PHOTO_PREFIX = "photos_"
VIDEO_PREFIX = "videos_"

PHOTO_TABLE = "photos_raw"
VIDEO_TABLE = "videos_raw"
LOG_TABLE = "ingested_files"

PHOTO_SCHEMA = """
CREATE TABLE IF NOT EXISTS photos_raw AS SELECT * FROM (SELECT ''::TEXT as SourceFile) WHERE FALSE;
"""
# We'll let DuckDB auto-create columns based on CSV import; using a staging read first.
VIDEO_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos_raw AS SELECT * FROM (SELECT ''::TEXT as SourceFile) WHERE FALSE;
"""
LOG_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
  file_path TEXT PRIMARY KEY,
  ingested_at TIMESTAMP DEFAULT current_timestamp
);
"""


def ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(PHOTO_SCHEMA)
    con.execute(VIDEO_SCHEMA)
    con.execute(LOG_SCHEMA)


def list_targets(directory: Path, prefix: str) -> list[Path]:
    return sorted(p for p in directory.glob(f"{prefix}*.csv") if p.is_file())


def already_ingested(con: duckdb.DuckDBPyConnection) -> set[str]:
    try:
        rows = con.execute(f"SELECT file_path FROM {LOG_TABLE}").fetchall()
    except duckdb.CatalogException:
        return set()
    return {r[0] for r in rows}


def ingest_file(con: duckdb.DuckDBPyConnection, path: Path, table: str) -> None:
    # Read CSV with auto-detected schema into a relation then append
    rel = con.read_csv(str(path), header=True, auto_detect=True)
    rel.create_view("_staging_ingest", replace=True)
    con.execute(f"INSERT INTO {table} SELECT * FROM _staging_ingest")
    con.execute("DROP VIEW _staging_ingest")
    con.execute("INSERT INTO ingested_files(file_path) VALUES (?)", [str(path)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="catalogue.duckdb", help="DuckDB database path")
    ap.add_argument("--dir", default="output", help="Directory containing CSV scan files")
    args = ap.parse_args()

    out_dir = Path(args.dir)
    if not out_dir.exists():
        raise SystemExit(f"Output directory not found: {out_dir}")

    con = duckdb.connect(args.db)
    ensure_schema(con)
    ingested = already_ingested(con)

    photo_files = list_targets(out_dir, PHOTO_PREFIX)
    video_files = list_targets(out_dir, VIDEO_PREFIX)

    added = 0
    for path in photo_files:
        if str(path) in ingested:
            continue
        ingest_file(con, path, PHOTO_TABLE)
        added += 1
    for path in video_files:
        if str(path) in ingested:
            continue
        ingest_file(con, path, VIDEO_TABLE)
        added += 1

    print(f"Ingestion complete. New files ingested: {added}")


if __name__ == "__main__":  # pragma: no cover
    main()
