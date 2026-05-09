from __future__ import annotations

import json
from pathlib import Path

import pytest

from disk_catalogue.semantic_audio import catalogue_audio


def test_catalogue_audio_processes_audio_files_with_injected_semantics(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    (root / "voice.wav").write_bytes(b"fake wav")
    (root / "notes.txt").write_text("not audio")
    nested = root / "album"
    nested.mkdir()
    (nested / "song.MP3").write_bytes(b"fake mp3")
    state_path = tmp_path / "semantic-audio-state.json"

    transcribed: list[str] = []

    def transcribe(path: Path) -> str:
        transcribed.append(path.relative_to(root).as_posix())
        return f"transcript for {path.stem.lower()}"

    def embed(text: str) -> list[float]:
        return [float(len(text)), 0.5]

    records = catalogue_audio(
        root,
        state_path,
        transcriber=transcribe,
        embedder=embed,
    )

    assert transcribed == ["album/song.MP3", "voice.wav"]
    assert [record.relative_path for record in records] == ["album/song.MP3", "voice.wav"]
    assert [record.transcript for record in records] == [
        "transcript for song",
        "transcript for voice",
    ]
    assert records[0].embedding == [19.0, 0.5]
    assert records[1].embedding == [20.0, 0.5]
    assert all(record.path.is_absolute() for record in records)

    state = json.loads(state_path.read_text())
    assert state["version"] == 1
    assert sorted(state["records"]) == ["album/song.MP3", "voice.wav"]
    assert state["records"]["voice.wav"]["transcript"] == "transcript for voice"
    assert state["records"]["voice.wav"]["embedding"] == [20.0, 0.5]


def test_catalogue_audio_resumes_completed_unchanged_files(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    audio = root / "interview.wav"
    audio.write_bytes(b"first version")
    state_path = tmp_path / "semantic-audio-state.json"

    calls: list[str] = []

    def transcribe(path: Path) -> str:
        calls.append(path.name)
        return f"semantic text {len(calls)}"

    def embed(text: str) -> list[float]:
        return [float(len(text))]

    first = catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)
    second = catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)

    assert calls == ["interview.wav"]
    assert second == first


def test_catalogue_audio_reprocesses_changed_files_but_keeps_other_state(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    unchanged = root / "unchanged.flac"
    changed = root / "changed.wav"
    unchanged.write_bytes(b"stable audio")
    changed.write_bytes(b"old audio")
    state_path = tmp_path / "semantic-audio-state.json"

    transcripts = {
        "unchanged.flac": "unchanged transcript",
        "changed.wav": "old transcript",
    }
    calls: list[str] = []

    def transcribe(path: Path) -> str:
        calls.append(path.name)
        return transcripts[path.name]

    def embed(text: str) -> list[float]:
        return [float(sum(ord(char) for char in text) % 100)]

    catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)
    changed.write_bytes(b"new audio bytes")
    transcripts["changed.wav"] = "new transcript"
    calls.clear()

    records = catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)

    assert calls == ["changed.wav"]
    by_name = {record.relative_path: record for record in records}
    assert by_name["unchanged.flac"].transcript == "unchanged transcript"
    assert by_name["changed.wav"].transcript == "new transcript"


def test_catalogue_audio_marks_failed_file_and_retries_on_next_run(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    (root / "ok.wav").write_bytes(b"ok audio")
    failing = root / "retry.wav"
    failing.write_bytes(b"retry audio")
    state_path = tmp_path / "semantic-audio-state.json"

    failures = {"retry.wav"}
    calls: list[str] = []

    def transcribe(path: Path) -> str:
        calls.append(path.name)
        if path.name in failures:
            raise RuntimeError("transcription failed")
        return f"transcript {path.name}"

    def embed(text: str) -> list[float]:
        return [float(len(text))]

    with pytest.raises(RuntimeError, match="transcription failed"):
        catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)

    state = json.loads(state_path.read_text())
    assert state["records"]["ok.wav"]["status"] == "completed"
    assert state["records"]["retry.wav"]["status"] == "failed"

    failures.clear()
    calls.clear()
    records = catalogue_audio(root, state_path, transcriber=transcribe, embedder=embed)

    assert calls == ["retry.wav"]
    assert [record.relative_path for record in records] == ["ok.wav", "retry.wav"]
    assert all(record.status == "completed" for record in records)
