from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int


def iter_files(root: Path) -> Iterator[Path]:
    for p in root.rglob('*'):
        if p.is_file():
            yield p


def scan_path(root: str | Path) -> Iterable[FileRecord]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(f"Path not found: {base}")
    for file_path in iter_files(base):
        try:
            size = file_path.stat().st_size
        except OSError:
            continue
        yield FileRecord(path=file_path, size=size)
