from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from disk_catalogue.audio_semantic import is_generic_title, normalise_space

DEFAULT_TARGET_ROOT = Path(
    "/Volumes/ExtSSD-Data/Avery Willis Storying Audio/Following Jesus - Renamed"
)
DEFAULT_RENAME_DIR = Path("output/recovery_plans/following_jesus_team_ext10/rename_fileset")
DEFAULT_PLAN_PATH = DEFAULT_RENAME_DIR / "following_jesus_rename_plan.csv"
DEFAULT_TRACK_CATALOGUE_PATH = DEFAULT_RENAME_DIR / "following_jesus_track_catalogue.csv"
DEFAULT_ALBUM_CATALOGUE_PATH = DEFAULT_RENAME_DIR / "following_jesus_album_catalogue.csv"
DEFAULT_MARKDOWN_CATALOGUE_PATH = DEFAULT_RENAME_DIR / "following_jesus_catalogue.md"
DEFAULT_VALIDATION_REPORT_PATH = DEFAULT_RENAME_DIR / "following_jesus_rename_validation.json"

PLAN_FIELDNAMES = [
    "file_key",
    "module_code",
    "module_title",
    "source_album_folder",
    "source_file_name",
    "disc_index",
    "track_index",
    "selected_title",
    "embedded_title",
    "semantic_title",
    "track_type",
    "bible_reference",
    "duration_seconds",
    "size_bytes",
    "source_sha256",
    "source_path",
    "target_relative_path",
    "target_path",
]


@dataclass(frozen=True)
class AlbumSpec:
    module_code: str
    module_title: str
    module_sort: int

    @property
    def folder_name(self) -> str:
        return f"{self.module_code} {self.module_title}"


@dataclass(frozen=True)
class RenameEntry:
    file_key: str
    module_code: str
    module_title: str
    module_sort: int
    source_album_folder: str
    source_file_name: str
    disc_index: int
    track_index: int
    selected_title: str
    embedded_title: str
    semantic_title: str
    track_type: str
    bible_reference: str
    duration_seconds: float | None
    size_bytes: int | None
    source_sha256: str
    source_path: str
    target_relative_path: str
    target_path: str

    def plan_row(self) -> dict[str, Any]:
        row = asdict(self)
        row.pop("module_sort")
        return row


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    file_key: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    mode: str
    total_rows: int
    source_present: int
    target_present: int
    ready_to_apply: int
    already_renamed: int
    missing: int
    issues: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "total_rows": self.total_rows,
            "source_present": self.source_present,
            "target_present": self.target_present,
            "ready_to_apply": self.ready_to_apply,
            "already_renamed": self.already_renamed,
            "missing": self.missing,
            "issues": [asdict(issue) for issue in self.issues],
        }


def parse_int(value: Any, default: int = 0) -> int:
    if value in (None, "", "nan"):
        return default
    return int(float(str(value)))


def parse_float(value: Any) -> float | None:
    if value in (None, "", "nan"):
        return None
    return float(str(value))


def parse_size(value: Any) -> int | None:
    if value in (None, "", "nan"):
        return None
    return int(float(str(value)))


def album_spec_for_folder(album_folder: str) -> AlbumSpec:
    folder = album_folder.casefold()
    if "making disciples" in folder or "primary oral" in folder:
        return AlbumSpec("FJ-M01", "Primary Oral Learners", 1)
    if "choosing to follow" in folder:
        return AlbumSpec("FJ-M02", "Choosing to Follow", 2)
    if "living in the family" in folder:
        return AlbumSpec("FJ-M03", "Living in the Family", 3)
    if "becoming like jesus" in folder:
        return AlbumSpec("FJ-M04", "Becoming Like Jesus", 4)
    if "serving like jesus" in folder:
        return AlbumSpec("FJ-M05", "Serving Like Jesus", 5)
    if "multiplying spiritual" in folder:
        return AlbumSpec("FJ-M06", "Multiplying Disciples", 6)
    if "mission with god" in folder:
        return AlbumSpec("FJ-M07", "Mission With God", 7)
    return AlbumSpec("FJ-M00", sanitise_title(album_folder, max_chars=48), 0)


def ascii_text(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value)
    return normalised.encode("ascii", "ignore").decode("ascii")


def sanitise_title(value: str, max_chars: int = 72) -> str:
    text = ascii_text(value).replace("&", " and ")
    text = re.sub(r"[/\\:*?\"<>|]+", " ", text)
    text = re.sub(r"[\[\](){}]+", " ", text)
    text = normalise_space(text).strip(" ._-")
    if not text:
        return "Untitled"
    if len(text) <= max_chars:
        return text
    shortened = text[:max_chars].rsplit(" ", 1)[0].strip(" ._-")
    return shortened or text[:max_chars].strip(" ._-")


def choose_track_title(row: Mapping[str, Any]) -> str:
    embedded = normalise_space(str(row.get("embedded_title") or ""))
    semantic = normalise_space(str(row.get("semantic_title") or ""))
    source_file_name = Path(str(row.get("source_file_name") or "")).stem
    if embedded and not is_generic_title(embedded):
        return embedded
    if semantic and not is_generic_title(semantic):
        return semantic
    return source_file_name or embedded or "Untitled"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_rename_entry(
    row: Mapping[str, Any],
    target_root: Path,
    include_hash: bool = False,
) -> RenameEntry:
    album = album_spec_for_folder(str(row["source_album_folder"]))
    disc_index = parse_int(row.get("disc_index"))
    track_index = parse_int(row.get("track_index"))
    selected_title = sanitise_title(choose_track_title(row))
    source_path = Path(str(row["source_path"]))
    file_ext = source_path.suffix.lower() or ".m4a"
    file_name = f"{album.module_code}-D{disc_index:02d}-T{track_index:02d} - {selected_title}"
    target_relative = Path(album.folder_name) / f"Disc {disc_index:02d}" / f"{file_name}{file_ext}"
    target_path = target_root / target_relative
    source_sha = file_sha256(source_path) if include_hash and source_path.exists() else ""

    return RenameEntry(
        file_key=str(row["file_key"]),
        module_code=album.module_code,
        module_title=album.module_title,
        module_sort=album.module_sort,
        source_album_folder=str(row["source_album_folder"]),
        source_file_name=str(row["source_file_name"]),
        disc_index=disc_index,
        track_index=track_index,
        selected_title=selected_title,
        embedded_title=str(row.get("embedded_title") or ""),
        semantic_title=str(row.get("semantic_title") or ""),
        track_type=str(row.get("track_type") or ""),
        bible_reference=str(row.get("bible_reference") or ""),
        duration_seconds=parse_float(row.get("duration_seconds")),
        size_bytes=parse_size(row.get("size_bytes")),
        source_sha256=source_sha,
        source_path=str(source_path),
        target_relative_path=str(target_relative),
        target_path=str(target_path),
    )


def ensure_unique_targets(entries: Sequence[RenameEntry]) -> None:
    counts = Counter(entry.target_path for entry in entries)
    duplicates = sorted(path for path, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate target paths in rename plan: {duplicates[:5]}")


def write_plan(path: Path, entries: Sequence[RenameEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_FIELDNAMES)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.plan_row())


def read_plan(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_plan_rows(
    rows: Sequence[Mapping[str, str]],
    mode: str = "auto",
    verify_hash: bool = False,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    source_present = 0
    target_present = 0
    ready_to_apply = 0
    already_renamed = 0
    missing = 0

    target_counts = Counter(row["target_path"] for row in rows)
    for target_path, count in target_counts.items():
        if count > 1:
            issues.append(
                ValidationIssue(
                    severity="error",
                    file_key="",
                    message=f"duplicate target path appears {count} times: {target_path}",
                )
            )

    for row in rows:
        file_key = row.get("file_key", "")
        source = Path(row["source_path"])
        target = Path(row["target_path"])
        size = parse_size(row.get("size_bytes"))
        has_source = source.exists()
        has_target = target.exists()
        source_present += int(has_source)
        target_present += int(has_target)

        if has_source and not has_target:
            ready_to_apply += 1
        elif has_target and not has_source:
            already_renamed += 1
        elif not has_source and not has_target:
            missing += 1
            issues.append(
                ValidationIssue("error", file_key, "neither source nor target exists")
            )
        elif source.resolve() != target.resolve():
            issues.append(
                ValidationIssue("error", file_key, "both source and target exist")
            )

        path_to_check = target if has_target else source
        if path_to_check.exists() and size is not None and path_to_check.stat().st_size != size:
            issues.append(
                ValidationIssue(
                    "error",
                    file_key,
                    f"size mismatch for {path_to_check}: expected {size}",
                )
            )
        if verify_hash and row.get("source_sha256") and path_to_check.exists():
            actual_hash = file_sha256(path_to_check)
            if actual_hash != row["source_sha256"]:
                issues.append(
                    ValidationIssue("error", file_key, "sha256 mismatch")
                )

    if mode == "before" and target_present:
        issues.append(ValidationIssue("error", "", "target files already exist"))
    if mode == "after" and ready_to_apply:
        issues.append(ValidationIssue("error", "", "source files still need renaming"))

    return ValidationReport(
        mode=mode,
        total_rows=len(rows),
        source_present=source_present,
        target_present=target_present,
        ready_to_apply=ready_to_apply,
        already_renamed=already_renamed,
        missing=missing,
        issues=issues,
    )


def apply_rename_plan(
    rows: Sequence[Mapping[str, str]],
    apply: bool = False,
) -> ValidationReport:
    report = validate_plan_rows(rows, mode="auto")
    if not report.ok:
        return report
    if not apply:
        return report
    for row in rows:
        source = Path(row["source_path"])
        target = Path(row["target_path"])
        if not source.exists() or target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
    return validate_plan_rows(rows, mode="after")


def write_json_report(path: Path, report: ValidationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_jsonable(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def album_catalogue_rows(entries: Sequence[RenameEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (module_sort, module_code, module_title), module_entries_iter in _group_entries(
        entries,
        key=lambda item: (item.module_sort, item.module_code, item.module_title),
    ):
        module_entries = list(module_entries_iter)
        rows.append(
            {
                "module_code": module_code,
                "module_title": module_title,
                "track_count": len(module_entries),
                "disc_count": len({entry.disc_index for entry in module_entries}),
                "source_album_folders": json.dumps(
                    sorted({entry.source_album_folder for entry in module_entries})
                ),
                "target_folder": f"{module_code} {module_title}",
                "module_sort": module_sort,
            }
        )
    return rows


def track_catalogue_rows(entries: Sequence[RenameEntry]) -> list[dict[str, Any]]:
    return [
        {
            "module_code": entry.module_code,
            "module_title": entry.module_title,
            "disc_index": entry.disc_index,
            "track_index": entry.track_index,
            "title": entry.selected_title,
            "track_type": entry.track_type,
            "bible_reference": entry.bible_reference,
            "duration_seconds": entry.duration_seconds,
            "file_key": entry.file_key,
            "original_path": entry.source_path,
            "renamed_path": entry.target_path,
        }
        for entry in entries
    ]


def write_dict_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_catalogue(path: Path, entries: Sequence[RenameEntry]) -> None:
    lines = ["# Following Jesus Audio Catalogue", ""]
    for album_row in album_catalogue_rows(entries):
        module_code = album_row["module_code"]
        module_title = album_row["module_title"]
        module_entries = [entry for entry in entries if entry.module_code == module_code]
        lines.extend(
            [
                f"## {module_code} {module_title}",
                "",
                f"{album_row['track_count']} tracks across {album_row['disc_count']} discs.",
                "",
            ]
        )
        current_disc: int | None = None
        for entry in sorted(
            module_entries,
            key=lambda item: (item.disc_index, item.track_index),
        ):
            if entry.disc_index != current_disc:
                current_disc = entry.disc_index
                lines.extend([f"### Disc {current_disc:02d}", ""])
            suffix = f" ({entry.bible_reference})" if entry.bible_reference else ""
            lines.append(f"- T{entry.track_index:02d} - {entry.selected_title}{suffix}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _group_entries(
    entries: Sequence[RenameEntry],
    key: Callable[[RenameEntry], Any],
) -> Iterable[tuple[Any, list[RenameEntry]]]:
    groups: dict[Any, list[RenameEntry]] = {}
    for entry in sorted(entries, key=key):
        groups.setdefault(key(entry), []).append(entry)
    return groups.items()
