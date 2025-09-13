#!/usr/bin/env python
"""Load latest scan CSVs into DuckDB tables.

Usage:
  python scripts/load_csvs.py [--db catalogue.duckdb] [--dir output]

Behavior:
  - Loads all matching CSVs (photos_*.csv, videos_*.csv) incrementally.
  - Creates target tables on first ingest using the CSV schema.
  - If schemas drift, adds missing columns and aligns on insert.
  - Skips files already recorded in an ingestion log table.
"""
from __future__ import annotations

import argparse
import duckdb
from pathlib import Path

PHOTO_PREFIX = "photos_"
VIDEO_PREFIX = "videos_"
FILE_PREFIX = "files_"

PHOTO_TABLE = "photos_raw"
VIDEO_TABLE = "videos_raw"
FILE_TABLE = "files_raw"
LOG_TABLE = "ingested_files"

LOG_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
  file_path TEXT PRIMARY KEY,
  ingested_at TIMESTAMP DEFAULT current_timestamp
);
"""


def ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(LOG_SCHEMA)


def list_targets(directory: Path, prefix: str) -> list[Path]:
    return sorted(p for p in directory.glob(f"{prefix}*.csv") if p.is_file())


def already_ingested(con: duckdb.DuckDBPyConnection) -> set[str]:
    try:
        rows = con.execute(f"SELECT file_path FROM {LOG_TABLE}").fetchall()
    except duckdb.CatalogException:
        return set()
    return {r[0] for r in rows}


def table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    q = """
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'main' AND table_name = ?
    LIMIT 1
    """
    return con.execute(q, [table]).fetchone() is not None


def get_table_columns(con: duckdb.DuckDBPyConnection, table: str) -> list[tuple[str, str]]:
    # Returns list of (name, type)
    rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    # duckdb pragma: cid, name, type, notnull, dflt_value, pk
    return [(r[1], r[2]) for r in rows]


def get_view_columns(con: duckdb.DuckDBPyConnection, view: str) -> list[tuple[str, str]]:
    rows = con.execute(f"DESCRIBE {view}").fetchall()
    # columns: column_name, column_type, null, key, default, extra
    return [(r[0], r[1]) for r in rows]


def qident(name: str) -> str:
    # Quote an identifier for DuckDB (handles spaces, #, :, - etc.)
    return '"' + name.replace('"', '""') + '"'


def ingest_file(con: duckdb.DuckDBPyConnection, path: Path, table: str) -> None:
    # Read CSV with auto-detected schema into a relation, create staging view
    rel = con.read_csv(str(path), header=True, auto_detect=True)
    rel.create_view("_staging_ingest", replace=True)

    try:
        if not table_exists(con, table):
            # Create target table with the same schema as the CSV (empty table)
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM _staging_ingest WHERE FALSE")
        else:
            # Align schemas if needed
            tgt_cols = get_table_columns(con, table)
            stg_cols = get_view_columns(con, "_staging_ingest")
            tgt_names = [n for n, _ in tgt_cols]
            stg_dict = {n: t for n, t in stg_cols}

            # Add any missing columns from staging to target (using staging type)
            for name, typ in stg_cols:
                if name not in tgt_names:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {qident(name)} {typ}")
            # Refresh target columns after ALTERs
            tgt_cols = get_table_columns(con, table)
            tgt_names = [n for n, _ in tgt_cols]

            # Build aligned select list over staging
            select_exprs: list[str] = []
            for name, typ in tgt_cols:
                if name in stg_dict:
                    select_exprs.append(qident(name))
                else:
                    select_exprs.append(f"NULL::{typ} AS {qident(name)}")

            select_sql = ", ".join(select_exprs)
            con.execute(f"INSERT INTO {table} SELECT {select_sql} FROM _staging_ingest")
            con.execute("DROP VIEW _staging_ingest")
            con.execute("INSERT INTO ingested_files(file_path) VALUES (?)", [str(path)])
            return

        # Fresh table path: insert all columns directly
        con.execute(f"INSERT INTO {table} SELECT * FROM _staging_ingest")
        con.execute("DROP VIEW _staging_ingest")
        con.execute("INSERT INTO ingested_files(file_path) VALUES (?)", [str(path)])
    except Exception:
        # Ensure staging view is dropped on error to avoid name clashes later
        try:
            con.execute("DROP VIEW _staging_ingest")
        except Exception:
            pass
        raise


def ensure_derived_views(con: duckdb.DuckDBPyConnection) -> None:
    # Create convenient views with derived identifiers and drive/path parsing
    con.execute(
        r'''
        CREATE OR REPLACE VIEW files AS
        SELECT
          *,
          regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1) AS Drive,
          regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', '') AS RelativePath,
          regexp_extract("Directory", '/host/Volumes/[^/]+/(.*)$', 1) AS RelativeDirectory,
          lower(regexp_extract("FileName", '\\.([^.]+)$', 1)) AS FileExt,
          hash(
            regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1),
            regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', ''),
            CAST("FileSize#" AS BIGINT)
          ) AS FileKey
        FROM files_raw;
        '''
    )
    con.execute(
        r'''
        CREATE OR REPLACE VIEW photos AS
        SELECT
          *,
          regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1) AS Drive,
          regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', '') AS RelativePath,
          regexp_extract("Directory", '/host/Volumes/[^/]+/(.*)$', 1) AS RelativeDirectory,
          lower(regexp_extract("FileName", '\\.([^.]+)$', 1)) AS FileExt,
          hash(
            regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1),
            regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', ''),
            CAST("FileSize#" AS BIGINT)
          ) AS FileKey
        FROM photos_raw;
        '''
    )
    con.execute(
        r'''
        CREATE OR REPLACE VIEW videos AS
        SELECT
          *,
          regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1) AS Drive,
          regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', '') AS RelativePath,
          regexp_extract("Directory", '/host/Volumes/[^/]+/(.*)$', 1) AS RelativeDirectory,
          lower(regexp_extract("FileName", '\\.([^.]+)$', 1)) AS FileExt,
          hash(
            regexp_extract("SourceFile", '/host/Volumes/([^/]+)/', 1),
            regexp_replace("SourceFile", '^/host/Volumes/[^/]+/', ''),
            CAST("FileSize#" AS BIGINT)
          ) AS FileKey
        FROM videos_raw;
        '''
    )


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
    file_files = list_targets(out_dir, FILE_PREFIX)

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
    for path in file_files:
        if str(path) in ingested:
            continue
        ingest_file(con, path, FILE_TABLE)
        added += 1

    # Create/refresh derived views for convenience and stable identifiers
    ensure_derived_views(con)
    print(f"Ingestion complete. New files ingested: {added}")


if __name__ == "__main__":  # pragma: no cover
    main()
