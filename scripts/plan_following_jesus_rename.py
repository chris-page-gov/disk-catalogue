#!/usr/bin/env python3
"""Generate a safe rename plan and catalogues for the Following Jesus audio files.

The command reads `audio_semantic_catalogue` and `audio_semantic_source_metadata` from
`catalogue.duckdb`, then writes:

- a rename plan CSV used by `scripts/rename_following_jesus_files.py`
- album and track catalogue CSVs
- a readable Markdown catalogue

By default it does not modify the files on the external SSD.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import duckdb

from disk_catalogue.following_jesus_rename import (
    DEFAULT_ALBUM_CATALOGUE_PATH,
    DEFAULT_MARKDOWN_CATALOGUE_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_TARGET_ROOT,
    DEFAULT_TRACK_CATALOGUE_PATH,
    RenameEntry,
    album_catalogue_rows,
    build_rename_entry,
    ensure_unique_targets,
    track_catalogue_rows,
    write_dict_csv,
    write_markdown_catalogue,
    write_plan,
)


def load_rows(db_path: Path) -> list[dict[str, Any]]:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            select
              m.file_key,
              m.destination_path as source_path,
              m.album_folder as source_album_folder,
              m.file_name as source_file_name,
              m.title as embedded_title,
              c.semantic_title,
              c.track_type,
              c.bible_reference,
              cast(m.disc_index as integer) as disc_index,
              cast(m.track_index as integer) as track_index,
              try_cast(m.duration_seconds as double) as duration_seconds,
              try_cast(m.size_bytes_actual as bigint) as size_bytes
            from audio_semantic_source_metadata m
            join audio_semantic_catalogue c using (file_key)
            order by m.album_folder, disc_index, track_index, m.file_name
            """
        ).fetchall()
        columns = [item[0] for item in con.description]
    finally:
        con.close()
    return [dict(zip(columns, row, strict=True)) for row in rows]


def build_entries(
    rows: list[dict[str, Any]],
    target_root: Path,
    include_hash: bool,
) -> list[RenameEntry]:
    entries = [build_rename_entry(row, target_root, include_hash=include_hash) for row in rows]
    ensure_unique_targets(entries)
    return sorted(
        entries,
        key=lambda item: (item.module_sort, item.disc_index, item.track_index, item.file_key),
    )


def write_rename_table(db_path: Path, plan_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    try:
        con.execute(
            """
            create or replace table audio_semantic_rename_plan as
            select * from read_csv_auto(?)
            """,
            [str(plan_path)],
        )
    finally:
        con.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("catalogue.duckdb"))
    parser.add_argument("--target-root", type=Path, default=DEFAULT_TARGET_ROOT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--track-catalogue", type=Path, default=DEFAULT_TRACK_CATALOGUE_PATH)
    parser.add_argument("--album-catalogue", type=Path, default=DEFAULT_ALBUM_CATALOGUE_PATH)
    parser.add_argument("--markdown-catalogue", type=Path, default=DEFAULT_MARKDOWN_CATALOGUE_PATH)
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Store source SHA-256 hashes in the plan for later validation.",
    )
    parser.add_argument(
        "--no-db-table",
        action="store_true",
        help="Do not replace the audio_semantic_rename_plan table in catalogue.duckdb.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    entries = build_entries(load_rows(args.db), args.target_root, include_hash=args.hash)
    write_plan(args.plan, entries)
    write_dict_csv(args.track_catalogue, track_catalogue_rows(entries))
    write_dict_csv(args.album_catalogue, album_catalogue_rows(entries))
    write_markdown_catalogue(args.markdown_catalogue, entries)
    if not args.no_db_table:
        write_rename_table(args.db, args.plan)
    print(
        f"planned {len(entries)} renames under {args.target_root}\n"
        f"plan: {args.plan}\n"
        f"track catalogue: {args.track_catalogue}\n"
        f"album catalogue: {args.album_catalogue}\n"
        f"markdown catalogue: {args.markdown_catalogue}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
