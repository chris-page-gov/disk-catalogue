#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from typing import List, Tuple

import duckdb


QUERY = """
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY drive_label ORDER BY started_at DESC) rn
  FROM drive_scans
)
SELECT drive_label,
       started_at AS last_started_at,
       ended_at   AS last_ended_at,
       status,
       files_rows, photos_rows, videos_rows,
       (epoch(ended_at) - epoch(started_at)) AS duration_s,
       files_rows + photos_rows + videos_rows AS total_rows,
       CASE WHEN (epoch(ended_at) - epoch(started_at)) > 0
            THEN ROUND((files_rows + photos_rows + videos_rows) * 1.0 / (epoch(ended_at) - epoch(started_at)), 2)
            ELSE NULL END AS rows_per_sec
FROM ranked
WHERE rn = 1
ORDER BY drive_label;
"""


def fmt_table(headers: List[str], rows: List[Tuple]) -> str:
    cols = list(zip(*([headers] + [["" if v is None else str(v) for v in r] for r in rows])))
    widths = [max(len(cell) for cell in col) for col in cols]
    def join_row(values: List[str]) -> str:
        return " | ".join(val.ljust(w) for val, w in zip(values, widths))

    lines = [join_row(headers), "-+-".join("-" * w for w in widths)]
    for r in rows:
        lines.append(join_row(["" if v is None else str(v) for v in r]))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Show last scan summary per drive from drive_scans")
    ap.add_argument("--db", default="catalogue.duckdb", help="DuckDB database path")
    ap.add_argument("--csv", action="store_true", help="Output as CSV instead of a table")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        raise SystemExit(f"Database not found: {args.db}")

    con = duckdb.connect(args.db)
    # Ensure table exists
    try:
        con.sql("SELECT 1 FROM information_schema.tables WHERE table_schema='main' AND table_name='drive_scans'")
    except Exception:
        raise SystemExit("drive_scans table not found. Run a scan via scripts/scan_and_ingest.py first.")

    res = con.sql(QUERY).fetchall()
    headers = [
        "drive_label",
        "last_started_at",
        "last_ended_at",
        "status",
        "files_rows",
        "photos_rows",
        "videos_rows",
        "duration_s",
        "total_rows",
        "rows_per_sec",
    ]
    if args.csv:
        import csv, sys
        w = csv.writer(sys.stdout)
        w.writerow(headers)
        for r in res:
            w.writerow(r)
    else:
        print(fmt_table(headers, res))


if __name__ == "__main__":  # pragma: no cover
    main()
