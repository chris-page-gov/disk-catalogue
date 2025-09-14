#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import duckdb


@dataclass(frozen=True)
class Requirement:
    name: str
    kind: str  # 'table' or 'view'
    required_columns: tuple[str, ...] = ()


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement("photos_raw", "table"),
    Requirement("videos_raw", "table"),
    Requirement("files_raw", "table"),
    Requirement("ingested_files", "table", ("file_path", "ingested_at")),
    Requirement("drives", "table", ("drive_label", "last_scanned")),
    Requirement("drive_scans", "table", ("drive_label", "started_at", "ended_at", "status")),
    Requirement(
        "files",
        "view",
        (
            "SourceFile",
            "FileName",
            "Directory",
            "FilePath",
            "FileSize#",
            "Drive",
            "RelativePath",
            "RelativeDirectory",
            "FileExt",
            "FileKey",
        ),
    ),
    Requirement(
        "photos",
        "view",
        (
            "SourceFile",
            "FileName",
            "Directory",
            "FilePath",
            "FileSize#",
            "Drive",
            "RelativePath",
            "RelativeDirectory",
            "FileExt",
            "FileKey",
        ),
    ),
    Requirement(
        "videos",
        "view",
        (
            "SourceFile",
            "FileName",
            "Directory",
            "FilePath",
            "FileSize#",
            "Drive",
            "RelativePath",
            "RelativeDirectory",
            "FileExt",
            "FileKey",
        ),
    ),
)


def list_relations(con: duckdb.DuckDBPyConnection) -> set[tuple[str, str]]:
    rows = con.sql(
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchall()
    return {(r[0], r[1].lower()) for r in rows}


def get_columns(con: duckdb.DuckDBPyConnection, name: str, kind: str) -> list[str]:
    if kind == "table":
        rows = con.sql(f"PRAGMA table_info('{name}')").fetchall()
        return [r[1] for r in rows]
    # view
    rows = con.sql(f"DESCRIBE {name}").fetchall()
    return [r[0] for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate DuckDB schema against repo expectations")
    ap.add_argument("--db", default="catalogue.duckdb", help="Path to DuckDB database")
    args = ap.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        raise SystemExit(f"Database not found: {db_path}")

    db_size_bytes = os.path.getsize(db_path)
    con = duckdb.connect(db_path)

    rels = list_relations(con)
    problems: list[str] = []

    print(f"Database: {db_path}")
    print(f"Size: {db_size_bytes / 1024 / 1024:.2f} MiB ({db_size_bytes} bytes)")
    print("")

    # Row counts (quick sanity)
    for tbl in ("files_raw", "photos_raw", "videos_raw"):
        if (tbl, "base table") in rels or (tbl, "table") in rels:
            row = con.sql(f"SELECT COUNT(*) FROM {tbl}").fetchone()
            n = int(row[0]) if row is not None else 0
            print(f"Rows in {tbl}: {n}")
    print("")

    for req in REQUIREMENTS:
        present = (req.name, "view" if req.kind == "view" else "base table") in rels or (
            req.name,
            req.kind,
        ) in rels
        if not present:
            problems.append(f"Missing {req.kind}: {req.name}")
            continue
        if req.required_columns:
            cols = get_columns(con, req.name, req.kind)
            missing = [c for c in req.required_columns if c not in cols]
            if missing:
                problems.append(f"{req.kind} {req.name} missing columns: {', '.join(missing)}")

    if problems:
        print("Schema validation: FAIL")
        for p in problems:
            print(f" - {p}")
        raise SystemExit(1)
    else:
        print("Schema validation: OK")


if __name__ == "__main__":  # pragma: no cover
    main()
