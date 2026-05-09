from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

AudioTranscriber = Callable[[Path], str]
TextEmbedder = Callable[[str], list[float]]

STATE_VERSION = 1
DEFAULT_AUDIO_EXTENSIONS = frozenset(
    {
        ".aac",
        ".aif",
        ".aiff",
        ".flac",
        ".m4a",
        ".mp3",
        ".ogg",
        ".opus",
        ".wav",
    }
)


@dataclass(frozen=True)
class AudioFingerprint:
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class SemanticAudioRecord:
    path: Path
    relative_path: str
    transcript: str
    embedding: list[float]
    status: str
    size: int
    mtime_ns: int
    error: str | None = None


def iter_audio_files(
    root: Path, audio_extensions: Sequence[str] = tuple(DEFAULT_AUDIO_EXTENSIONS)
) -> list[Path]:
    extensions = {extension.lower() for extension in audio_extensions}
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def fingerprint(path: Path) -> AudioFingerprint:
    stat = path.stat()
    return AudioFingerprint(size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {"version": STATE_VERSION, "records": {}}
    try:
        state = cast(dict[str, Any], json.loads(state_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return {"version": STATE_VERSION, "records": {}}
    if state.get("version") != STATE_VERSION or not isinstance(state.get("records"), dict):
        return {"version": STATE_VERSION, "records": {}}
    return state


def write_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp_path, state_path)


def state_record_matches(record: dict[str, Any], current: AudioFingerprint) -> bool:
    return (
        record.get("status") == "completed"
        and int(record.get("size", -1)) == current.size
        and int(record.get("mtime_ns", -1)) == current.mtime_ns
    )


def record_from_state(
    root: Path, relative_path: str, record: dict[str, Any]
) -> SemanticAudioRecord:
    return SemanticAudioRecord(
        path=(root / relative_path).resolve(),
        relative_path=relative_path,
        transcript=str(record.get("transcript", "")),
        embedding=[float(value) for value in record.get("embedding", [])],
        status=str(record.get("status", "unknown")),
        size=int(record.get("size", 0)),
        mtime_ns=int(record.get("mtime_ns", 0)),
        error=record.get("error"),
    )


def completed_state_record(
    transcript: str, embedding: list[float], current: AudioFingerprint
) -> dict[str, Any]:
    return {
        "status": "completed",
        "transcript": transcript,
        "embedding": embedding,
        "size": current.size,
        "mtime_ns": current.mtime_ns,
        "error": None,
    }


def failed_state_record(error: Exception, current: AudioFingerprint) -> dict[str, Any]:
    return {
        "status": "failed",
        "transcript": "",
        "embedding": [],
        "size": current.size,
        "mtime_ns": current.mtime_ns,
        "error": str(error),
    }


def catalogue_audio(
    root: str | Path,
    state_path: str | Path,
    *,
    transcriber: AudioTranscriber,
    embedder: TextEmbedder,
    audio_extensions: Sequence[str] = tuple(DEFAULT_AUDIO_EXTENSIONS),
) -> list[SemanticAudioRecord]:
    """Catalogue audio files under root with resumable JSON state.

    The expensive work is injected through `transcriber` and `embedder`, keeping
    this core deterministic and easy to test. Completed records are reused only
    while file size and mtime are unchanged. Failed records are retried.
    """

    root_path = Path(root)
    state_file = Path(state_path)
    state = load_state(state_file)
    records_state = state["records"]
    audio_files = iter_audio_files(root_path, audio_extensions)

    for path in audio_files:
        relative_path = path.relative_to(root_path).as_posix()
        current = fingerprint(path)
        previous = records_state.get(relative_path)
        if isinstance(previous, dict) and state_record_matches(previous, current):
            continue

        try:
            transcript = transcriber(path)
            embedding = embedder(transcript)
            records_state[relative_path] = completed_state_record(transcript, embedding, current)
            write_state(state_file, state)
        except Exception as exc:
            records_state[relative_path] = failed_state_record(exc, current)
            write_state(state_file, state)
            raise

    completed_records: list[SemanticAudioRecord] = []
    for path in audio_files:
        relative_path = path.relative_to(root_path).as_posix()
        if records_state.get(relative_path, {}).get("status") == "completed":
            completed_records.append(
                record_from_state(root_path, relative_path, records_state[relative_path])
            )
    return completed_records


def records_as_dicts(records: Sequence[SemanticAudioRecord]) -> list[dict[str, Any]]:
    return [
        {
            **asdict(record),
            "path": str(record.path),
        }
        for record in records
    ]
