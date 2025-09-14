from pathlib import Path

from disk_catalogue import scan_path


def test_scan_path_counts_tmp_files(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "a.txt").write_text("hello")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"123456")

    # Act
    records = list(scan_path(tmp_path))

    # Assert
    sizes = {r.path.name: r.size for r in records}
    assert sizes["a.txt"] == 5
    assert sizes["b.bin"] == 6
    assert len(records) == 2


def test_scan_path_missing() -> None:
    missing = Path("/unlikely/to/exist/___not_here___")
    try:
        list(scan_path(missing))
    except FileNotFoundError as e:
        assert str(missing) in str(e)
    else:
        raise AssertionError("Expected FileNotFoundError")
