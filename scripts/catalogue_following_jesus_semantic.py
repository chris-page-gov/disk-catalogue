#!/usr/bin/env python3
"""Build a resumable semantic catalogue for the Following Jesus audio recovery set.

Inputs:
  output/recovery_plans/following_jesus_team_ext10/audio_metadata.csv
  output/models/ggml-base.en.bin
  /Volumes/ExtSSD-Data/... copied M4A files

Outputs:
  output/recovery_plans/following_jesus_team_ext10/semantic_catalogue/
  catalogue.duckdb tables: audio_semantic_catalogue, audio_semantic_catalogue_status,
  audio_semantic_catalogue_verification, audio_semantic_catalogue_eval

The command is resumable. It writes JSON status after each file, skips completed unchanged
transcripts, keeps per-file semantic sidecars, and continues after individual failures.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from disk_catalogue.audio_semantic import (
    AudioCatalogueRecord,
    SemanticEntry,
    build_semantic_entry,
    load_gold_questions,
    score_gold_questions,
    semantic_entry_from_mapping,
    semantic_entry_row,
    transcript_output_stem,
    utc_now_iso,
    verify_catalogue_outputs,
)

PLAN_DIR = Path("output/recovery_plans/following_jesus_team_ext10")
DEFAULT_METADATA_CSV = PLAN_DIR / "audio_metadata.csv"
DEFAULT_OUTPUT_DIR = PLAN_DIR / "semantic_catalogue"
DEFAULT_DB = Path("catalogue.duckdb")
DEFAULT_MODEL = Path("output/models/ggml-base.en.bin")
DEFAULT_GOLD = Path("eval/following_jesus_gold_questions.json")
STATE_VERSION = 1


def int_or_none(value: str | None) -> int | None:
    if value in (None, "", "nan"):
        return None
    return int(float(value))


def float_or_none(value: str | None) -> float | None:
    if value in (None, "", "nan"):
        return None
    return float(value)


def load_records(metadata_csv: Path) -> list[AudioCatalogueRecord]:
    with metadata_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    records = [
        AudioCatalogueRecord(
            recovery_set=row["recovery_set"],
            file_key=str(row["file_key"]),
            album_folder=row["album_folder"],
            file_name=row["file_name"],
            title=row["title"],
            destination_path=row["destination_path"],
            disc_index=int_or_none(row.get("disc_index")),
            track_index=int_or_none(row.get("track_index")),
            duration_seconds=float_or_none(row.get("duration_seconds")),
        )
        for row in rows
    ]
    return sorted(
        records,
        key=lambda item: (item.album_folder, item.disc_index or 0, item.track_index or 0),
    )


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": STATE_VERSION, "records": {}, "created_at": utc_now_iso()}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_suffix(f".corrupt.{int(time.time())}.json")
        path.rename(backup)
        return {"version": STATE_VERSION, "records": {}, "created_at": utc_now_iso()}
    if state.get("version") != STATE_VERSION or not isinstance(state.get("records"), dict):
        return {"version": STATE_VERSION, "records": {}, "created_at": utc_now_iso()}
    return state


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def source_fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def transcript_paths(record: AudioCatalogueRecord, output_dir: Path) -> tuple[Path, Path, Path]:
    stem = transcript_output_stem(record, output_dir)
    return stem.with_suffix(".txt"), stem.with_suffix(".srt"), stem.with_suffix(".semantic.json")


def state_is_complete(record_state: dict[str, Any], source_fp: dict[str, Any]) -> bool:
    return (
        record_state.get("status") == "completed"
        and record_state.get("source_size") == source_fp["size"]
        and record_state.get("source_mtime_ns") == source_fp["mtime_ns"]
        and record_state.get("transcript_path")
        and Path(record_state["transcript_path"]).exists()
        and record_state.get("semantic_path")
        and Path(record_state["semantic_path"]).exists()
    )


def convert_to_wav(source: Path, wav_path: Path) -> None:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-sample_fmt",
            "s16",
            str(wav_path),
        ],
        check=True,
    )


def run_whisper(wav_path: Path, output_stem: Path, model_path: Path, threads: int) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "whisper-cli",
        "-m",
        str(model_path),
        "-f",
        str(wav_path),
        "-l",
        "en",
        "-t",
        str(threads),
        "-otxt",
        "-osrt",
        "-oj",
        "-of",
        str(output_stem),
        "-np",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        details = "\n".join(part for part in [result.stdout, result.stderr] if part)
        raise RuntimeError(f"whisper-cli failed for {wav_path}: {details[-4000:]}")


def transcribe_record(
    record: AudioCatalogueRecord,
    output_dir: Path,
    model_path: Path,
    threads: int,
) -> tuple[str, Path, Path | None]:
    transcript_path, srt_path, _semantic_path = transcript_paths(record, output_dir)
    if transcript_path.exists() and transcript_path.stat().st_size > 0:
        srt = srt_path if srt_path.exists() else None
        return transcript_path.read_text(encoding="utf-8"), transcript_path, srt

    source = Path(record.destination_path)
    output_stem = transcript_path.with_suffix("")
    with tempfile.TemporaryDirectory(prefix="following-jesus-audio-") as tmp_dir:
        wav_path = Path(tmp_dir) / f"{record.file_key}.wav"
        convert_to_wav(source, wav_path)
        run_whisper(wav_path, output_stem, model_path, threads)

    transcript_text = transcript_path.read_text(encoding="utf-8")
    return transcript_text, transcript_path, srt_path if srt_path.exists() else None


def load_entries(
    output_dir: Path, allowed_file_keys: set[str] | None = None
) -> dict[str, SemanticEntry]:
    entries: dict[str, SemanticEntry] = {}
    for path in sorted(output_dir.glob("transcripts/**/*.semantic.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        entry = semantic_entry_from_mapping(row)
        if allowed_file_keys is None or entry.file_key in allowed_file_keys:
            entries[entry.file_key] = entry
    return entries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_outputs(
    db_path: Path,
    output_dir: Path,
    records: list[AudioCatalogueRecord],
    state: dict[str, Any],
    gold_path: Path | None,
) -> None:
    expected_file_keys = {record.file_key for record in records}
    entries = load_entries(output_dir, expected_file_keys)
    entry_rows = [semantic_entry_row(entries[key]) for key in sorted(entries)]
    state_rows = [
        {"file_key": file_key, **record_state}
        for file_key, record_state in sorted(state["records"].items())
    ]
    transcript_map = {
        record.file_key: transcript_paths(record, output_dir)[0] for record in records
    }
    srt_map = {record.file_key: transcript_paths(record, output_dir)[1] for record in records}
    verification = verify_catalogue_outputs(records, entries, transcript_map, srt_map)
    verification_row = asdict(verification)

    write_csv(output_dir / "semantic_catalogue.csv", entry_rows)
    write_csv(output_dir / "semantic_catalogue_status.csv", state_rows)
    write_json_atomic(output_dir / "semantic_catalogue_verification.json", verification_row)

    eval_rows: list[dict[str, Any]] = []
    if gold_path is not None and gold_path.exists():
        scores = score_gold_questions(load_gold_questions(gold_path), list(entries.values()))
        eval_rows = [
            {
                "question_id": score.question_id,
                "score": score.score,
                "max_score": score.max_score,
                "passed": score.passed,
                "details_json": json.dumps(score.details, sort_keys=True),
            }
            for score in scores
        ]
        write_csv(output_dir / "semantic_catalogue_evaluation.csv", eval_rows)

    con = duckdb.connect(str(db_path))
    try:
        for table_name, rows in {
            "audio_semantic_catalogue": entry_rows,
            "audio_semantic_catalogue_status": state_rows,
            "audio_semantic_catalogue_verification": [verification_row],
            "audio_semantic_catalogue_eval": eval_rows,
        }.items():
            df = pd.DataFrame(rows)
            con.register("incoming_df", df)
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM incoming_df")
            con.unregister("incoming_df")
    finally:
        con.close()


def load_speaker_names(db_path: Path) -> dict[str, list[str]]:
    if not db_path.exists():
        return {}
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        table_exists = con.execute("""
            select count(*)
            from information_schema.tables
            where table_name = 'audio_speaker_assignments'
            """).fetchone()[0]
        if not table_exists:
            return {}
        rows = con.execute("""
            select cast(file_key as varchar) as file_key, assigned_speaker_name
            from audio_speaker_assignments
            where assignment_confidence in ('high', 'medium')
              and assigned_speaker_name is not null
              and assigned_speaker_name <> 'Unknown'
            order by file_key, assigned_speaker_name
            """).fetchall()
    finally:
        con.close()

    speakers: dict[str, list[str]] = {}
    for file_key, speaker_name in rows:
        names = speakers.setdefault(str(file_key), [])
        if speaker_name not in names:
            names.append(speaker_name)
    return speakers


def status_summary(records: list[AudioCatalogueRecord], state: dict[str, Any]) -> dict[str, Any]:
    states = state.get("records", {})
    expected_file_keys = {record.file_key for record in records}
    expected_states = [item for file_key, item in states.items() if file_key in expected_file_keys]
    completed = sum(1 for item in expected_states if item.get("status") == "completed")
    failed = sum(1 for item in expected_states if item.get("status") == "failed")
    running = sum(1 for item in expected_states if item.get("status") == "running")
    return {
        "total": len(records),
        "completed": completed,
        "failed": failed,
        "running": running,
        "remaining": max(0, len(records) - completed - failed),
        "updated_at": state.get("updated_at"),
        "last_file": state.get("last_file"),
    }


def print_status(records: list[AudioCatalogueRecord], state: dict[str, Any]) -> None:
    summary = status_summary(records, state)
    print(json.dumps(summary, indent=2, sort_keys=True))


def process_records(args: argparse.Namespace) -> int:
    records = load_records(args.metadata_csv)
    if args.file_key:
        wanted = {str(file_key) for file_key in args.file_key}
        records = [record for record in records if record.file_key in wanted]
    if args.limit:
        records = records[: args.limit]

    output_dir: Path = args.output_dir
    state_path = output_dir / "semantic_catalogue_state.json"
    state = load_state(state_path)
    state["total_files"] = len(records)
    state["updated_at"] = utc_now_iso()
    write_json_atomic(state_path, state)

    if args.status:
        print_status(records, state)
        return 0

    if args.verify or args.evaluate:
        export_outputs(args.db, output_dir, records, state, args.gold_questions)
        print_status(records, state)
        return 0

    speaker_names_by_file = load_speaker_names(args.db)
    failures = 0
    processed_since_export = 0
    for index, record in enumerate(records, start=1):
        source = Path(record.destination_path)
        record_state = state["records"].get(record.file_key, {})

        if not source.exists():
            state["records"][record.file_key] = {
                **record_state,
                "status": "failed",
                "error": f"missing source: {source}",
                "updated_at": utc_now_iso(),
            }
            failures += 1
            write_json_atomic(state_path, state)
            continue

        source_fp = source_fingerprint(source)
        if not args.force and state_is_complete(record_state, source_fp):
            continue
        if record_state.get("status") == "failed" and not args.retry_failed and not args.force:
            continue

        started = time.perf_counter()
        state["records"][record.file_key] = {
            **record_state,
            "status": "running",
            "source_size": source_fp["size"],
            "source_mtime_ns": source_fp["mtime_ns"],
            "started_at": utc_now_iso(),
            "album_folder": record.album_folder,
            "file_name": record.file_name,
            "title": record.title,
        }
        state["last_file"] = record.file_key
        state["updated_at"] = utc_now_iso()
        write_json_atomic(state_path, state)

        try:
            transcript_text, transcript_path, srt_path = transcribe_record(
                record, output_dir, args.model, args.threads
            )
            _txt, _srt, semantic_path = transcript_paths(record, output_dir)
            entry = build_semantic_entry(
                record,
                transcript_text,
                transcript_path,
                srt_path,
                speaker_names=speaker_names_by_file.get(record.file_key),
            )
            semantic_path.write_text(
                json.dumps(semantic_entry_row(entry), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            elapsed = round(time.perf_counter() - started, 3)
            state["records"][record.file_key] = {
                **state["records"][record.file_key],
                "status": "completed",
                "error": None,
                "completed_at": utc_now_iso(),
                "elapsed_seconds": elapsed,
                "transcript_path": str(transcript_path),
                "srt_path": str(srt_path) if srt_path else None,
                "semantic_path": str(semantic_path),
                "semantic_title": entry.semantic_title,
                "track_type": entry.track_type,
                "bible_reference": entry.bible_reference,
                "metadata_confidence": entry.metadata_confidence,
            }
            processed_since_export += 1
            print(
                f"[{index}/{len(records)}] completed {record.album_folder} / "
                f"{record.file_name} -> {entry.semantic_title}",
                flush=True,
            )
        except Exception as exc:
            failures += 1
            state["records"][record.file_key] = {
                **state["records"][record.file_key],
                "status": "failed",
                "error": repr(exc),
                "failed_at": utc_now_iso(),
            }
            print(
                f"[{index}/{len(records)}] failed {record.album_folder} / "
                f"{record.file_name}: {exc}",
                file=sys.stderr,
                flush=True,
            )

        state["updated_at"] = utc_now_iso()
        write_json_atomic(state_path, state)

        if processed_since_export >= args.checkpoint_interval:
            export_outputs(args.db, output_dir, records, state, args.gold_questions)
            processed_since_export = 0

    export_outputs(args.db, output_dir, records, state, args.gold_questions)
    print_status(records, state)
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-csv", type=Path, default=DEFAULT_METADATA_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--gold-questions", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--file-key",
        action="append",
        help="Process only a specific file_key. Repeat for multiple keys.",
    )
    parser.add_argument("--checkpoint-interval", type=int, default=25)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--retry-failed", action="store_true", default=True)
    parser.add_argument("--no-retry-failed", action="store_false", dest="retry_failed")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return process_records(args)


if __name__ == "__main__":
    raise SystemExit(main())
