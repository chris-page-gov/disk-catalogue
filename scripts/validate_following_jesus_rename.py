#!/usr/bin/env python3
"""Validate a Following Jesus rename plan before or after applying it."""

from __future__ import annotations

import argparse
from pathlib import Path

from disk_catalogue.following_jesus_rename import (
    DEFAULT_PLAN_PATH,
    DEFAULT_VALIDATION_REPORT_PATH,
    read_plan,
    validate_plan_rows,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument(
        "--mode",
        choices=["before", "after", "auto"],
        default="auto",
        help="Use before for pre-rename, after for post-rename, or auto for either state.",
    )
    parser.add_argument(
        "--verify-hash",
        action="store_true",
        help="Verify SHA-256 hashes when the plan contains source_sha256 values.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = validate_plan_rows(read_plan(args.plan), mode=args.mode, verify_hash=args.verify_hash)
    write_json_report(args.report, report)
    print(
        f"validation: ok={report.ok} mode={args.mode} rows={report.total_rows} "
        f"source_present={report.source_present} target_present={report.target_present} "
        f"ready_to_apply={report.ready_to_apply} already_renamed={report.already_renamed} "
        f"missing={report.missing} issues={len(report.issues)}"
    )
    print(f"report: {args.report}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
