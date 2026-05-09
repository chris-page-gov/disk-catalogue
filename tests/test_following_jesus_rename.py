from __future__ import annotations

import json
from pathlib import Path

from disk_catalogue.following_jesus_rename import (
    album_catalogue_rows,
    album_spec_for_folder,
    apply_rename_plan,
    build_rename_entry,
    choose_track_title,
    ensure_unique_targets,
    parse_float,
    parse_int,
    parse_size,
    read_plan,
    sanitise_title,
    track_catalogue_rows,
    validate_plan_rows,
    write_dict_csv,
    write_json_report,
    write_markdown_catalogue,
    write_plan,
)


def make_row(source: Path, title: str = "Track 03") -> dict[str, object]:
    return {
        "file_key": "k1",
        "source_path": str(source),
        "source_album_folder": "Following Jesus 2--Living in the Family",
        "source_file_name": "1-03 Track 03.m4a",
        "embedded_title": title,
        "semantic_title": "Jesus restores Peter: feed my sheep and follow me",
        "track_type": "bible_story",
        "bible_reference": "John 21:1-22",
        "disc_index": 1,
        "track_index": 3,
        "duration_seconds": 123.4,
        "size_bytes": source.stat().st_size if source.exists() else 1,
    }


def test_album_mapping_corrects_living_in_family_module_number() -> None:
    spec = album_spec_for_folder("Following Jesus 2--Living in the Family")

    assert spec.module_code == "FJ-M03"
    assert spec.folder_name == "FJ-M03 Living in the Family"


def test_album_mapping_covers_known_and_unknown_modules() -> None:
    cases = {
        "Following Jesus--Making Disciples Of Pri": "FJ-M01",
        "Following Jesus 2--Choosing to Follow": "FJ-M02",
        "Following Jesus 4--Becoming Like Jesus": "FJ-M04",
        "Following Jesus 5--Serving Like Jesus": "FJ-M05",
        "Following Jesus 6--Multiplying Spiritual": "FJ-M06",
        "Following Jesus 7--Our Mission With God": "FJ-M07",
        "Unexpected/Album:Name": "FJ-M00",
    }

    assert {
        album: album_spec_for_folder(album).module_code for album in cases
    } == cases


def test_parse_helpers_handle_empty_values() -> None:
    assert parse_int("") == 0
    assert parse_int("3.0") == 3
    assert parse_float("") is None
    assert parse_float("3.5") == 3.5
    assert parse_size(None) is None
    assert parse_size("42.0") == 42


def test_title_choice_and_sanitising() -> None:
    assert sanitise_title('A/B: "Long" Title?') == "A B Long Title"
    assert sanitise_title("") == "Untitled"
    assert sanitise_title("word " * 40, max_chars=20) == "word word word word"
    assert (
        choose_track_title(
            {
                "embedded_title": "Track 07",
                "semantic_title": "A compact semantic title",
                "source_file_name": "x.m4a",
            }
        )
        == "A compact semantic title"
    )
    assert (
        choose_track_title(
            {
                "embedded_title": "Wake Up To Orality And Literacy",
                "semantic_title": "Other",
                "source_file_name": "x.m4a",
            }
        )
        == "Wake Up To Orality And Literacy"
    )
    assert (
        choose_track_title(
            {
                "embedded_title": "",
                "semantic_title": "",
                "source_file_name": "fallback.m4a",
            }
        )
        == "fallback"
    )


def test_build_entry_and_catalogue_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.m4a"
    source.write_bytes(b"audio")
    entry = build_rename_entry(make_row(source), tmp_path / "renamed", include_hash=True)

    assert entry.module_code == "FJ-M03"
    assert entry.source_sha256
    assert entry.target_relative_path == (
        "FJ-M03 Living in the Family/Disc 01/"
        "FJ-M03-D01-T03 - Jesus restores Peter feed my sheep and follow me.m4a"
    )
    assert album_catalogue_rows([entry])[0]["track_count"] == 1
    assert track_catalogue_rows([entry])[0]["bible_reference"] == "John 21:1-22"

    markdown = tmp_path / "catalogue.md"
    write_markdown_catalogue(markdown, [entry])
    assert "FJ-M03 Living in the Family" in markdown.read_text(encoding="utf-8")

    empty_csv = tmp_path / "empty.csv"
    write_dict_csv(empty_csv, [])
    assert empty_csv.read_text(encoding="utf-8") == ""


def test_plan_validation_and_apply(tmp_path: Path) -> None:
    source = tmp_path / "source.m4a"
    source.write_bytes(b"audio")
    entry = build_rename_entry(make_row(source), tmp_path / "renamed")
    plan = tmp_path / "plan.csv"
    write_plan(plan, [entry])
    rows = read_plan(plan)

    before = validate_plan_rows(rows, mode="before")
    assert before.ok
    assert before.ready_to_apply == 1

    dry_run = apply_rename_plan(rows)
    assert dry_run.ok
    assert source.exists()

    after = apply_rename_plan(rows, apply=True)
    assert after.ok
    assert not source.exists()
    assert Path(entry.target_path).exists()
    assert validate_plan_rows(rows, mode="after").ok


def test_validation_reports_missing_and_duplicate_targets(tmp_path: Path) -> None:
    missing = tmp_path / "missing.m4a"
    target = tmp_path / "target.m4a"
    row = make_row(missing)
    row["size_bytes"] = 1
    entry_one = build_rename_entry(row, tmp_path)
    entry_two = build_rename_entry({**row, "file_key": "k2"}, tmp_path)

    report = validate_plan_rows(
        [
            {key: str(value) for key, value in entry_one.plan_row().items()},
            {key: str(value) for key, value in entry_two.plan_row().items()},
        ]
    )

    assert not report.ok
    assert report.missing == 2
    assert any("duplicate target path" in issue.message for issue in report.issues)
    assert not target.exists()
    assert json.loads(json.dumps(report.to_jsonable()))["ok"] is False

    try:
        ensure_unique_targets([entry_one, entry_two])
    except ValueError as exc:
        assert "duplicate target paths" in str(exc)
    else:
        raise AssertionError("expected duplicate target exception")


def test_validation_modes_size_hash_and_report_file(tmp_path: Path) -> None:
    source = tmp_path / "source.m4a"
    source.write_bytes(b"audio")
    target_root = tmp_path / "renamed"
    entry = build_rename_entry(make_row(source), target_root, include_hash=True)
    row = {key: str(value) for key, value in entry.plan_row().items()}

    target = Path(entry.target_path)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"wrong-size")
    both_report = validate_plan_rows([row])
    assert not both_report.ok
    assert any(issue.message == "both source and target exist" for issue in both_report.issues)

    source.unlink()
    before_report = validate_plan_rows([row], mode="before")
    assert not before_report.ok
    assert any("target files already exist" in issue.message for issue in before_report.issues)

    size_report = validate_plan_rows([row], mode="after")
    assert not size_report.ok
    assert any("size mismatch" in issue.message for issue in size_report.issues)

    target.write_bytes(b"audio")
    hash_report = validate_plan_rows(
        [{**row, "source_sha256": "not-a-real-hash"}],
        mode="after",
        verify_hash=True,
    )
    assert not hash_report.ok
    assert any(issue.message == "sha256 mismatch" for issue in hash_report.issues)

    ok_report = validate_plan_rows([row], mode="after", verify_hash=True)
    assert ok_report.ok

    report_path = tmp_path / "report.json"
    write_json_report(report_path, ok_report)
    assert json.loads(report_path.read_text(encoding="utf-8"))["ok"] is True


def test_apply_rename_plan_returns_errors_without_moving(tmp_path: Path) -> None:
    source = tmp_path / "source.m4a"
    source.write_bytes(b"audio")
    entry = build_rename_entry(make_row(source), tmp_path / "renamed")
    row = {key: str(value) for key, value in entry.plan_row().items()}
    target = Path(entry.target_path)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"existing")

    report = apply_rename_plan([row], apply=True)

    assert not report.ok
    assert source.exists()
