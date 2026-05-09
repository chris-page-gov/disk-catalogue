#!/usr/bin/env python3
"""Apply or dry-run the Following Jesus file rename plan.

The command is deliberately conservative:

- dry-run is the default
- `--apply` is required to move files
- existing targets are treated as collisions
- source/target sizes are validated before and after
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from disk_catalogue.following_jesus_rename import (
    DEFAULT_PLAN_PATH,
    DEFAULT_VALIDATION_REPORT_PATH,
    apply_rename_plan,
    read_plan,
    write_json_report,
)


def write_apply_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["file_key", "source_path", "target_path"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "file_key": row["file_key"],
                    "source_path": row["source_path"],
                    "target_path": row["target_path"],
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files. Without this flag the command only validates the plan.",
    )
    parser.add_argument(
        "--apply-log",
        type=Path,
        default=DEFAULT_PLAN_PATH.with_name("following_jesus_rename_applied_log.csv"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = read_plan(args.plan)
    report = apply_rename_plan(rows, apply=args.apply)
    write_json_report(args.report, report)
    if args.apply and report.ok:
        write_apply_log(args.apply_log, rows)
    action = "applied" if args.apply else "dry-run"
    print(
        f"{action}: ok={report.ok} rows={report.total_rows} "
        f"ready_to_apply={report.ready_to_apply} already_renamed={report.already_renamed} "
        f"missing={report.missing} issues={len(report.issues)}"
    )
    print(f"report: {args.report}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
