import pytest
from pathlib import Path
from typing import Iterator, cast

import disk_catalogue.scanner as scanner
from disk_catalogue import scan_path


def test_scan_path_skips_on_oserror(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"):
    # Create one real file
    (tmp_path / "good.txt").write_text("ok")

    # Prepare a fake path object whose stat() raises OSError
    class BadPath:
        name = "bad"

        def stat(self):
            raise OSError("simulated stat failure")

    # Capture the real files from the real iter_files behaviour
    real_files: list[Path] = [p for p in tmp_path.rglob("*") if p.is_file()]

    def fake_iter_files(root: Path) -> Iterator[Path]:
        for p in real_files:
            yield p
        # Cast BadPath to Path so the generator return type matches Iterator[Path]
        yield cast(Path, BadPath())

    # Monkeypatch iter_files to include our bad path
    monkeypatch.setattr(scanner, "iter_files", fake_iter_files)

    records = list(scan_path(tmp_path))

    # Only the real file should be returned; the bad path is skipped
    assert len(records) == 1
    assert records[0].path.name == "good.txt"
