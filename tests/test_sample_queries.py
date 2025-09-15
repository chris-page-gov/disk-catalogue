from __future__ import annotations

import os
from pathlib import Path

import pytest


def have_duckdb() -> bool:
    try:
        import duckdb  # noqa: F401
    except Exception:
        return False
    return True


@pytest.mark.skipif(not have_duckdb(), reason="duckdb Python package not available")
def test_top_cameras_and_lenses() -> None:
    """Execute the "Top cameras and lenses" example from sample_queries.sql.

    Asserts the query runs, returns the expected columns, and that counts are
    sorted in non-increasing order.
    """
    import duckdb

    # Allow overriding DB path via env for CI/local variations
    db_path = Path(os.getenv("DISK_CATALOGUE_DB", "catalogue.duckdb"))
    if not db_path.exists():
        pytest.skip(f"database not found: {db_path}")

    con = duckdb.connect(str(db_path))
    # Ensure the photos view exists; otherwise skip gracefully
    exists = con.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'photos' LIMIT 1
        """
    ).fetchone()
    if not exists:
        pytest.skip("photos view not found; run ingestion first")

    # If Model/LensModel columns are not present (older scans with minimal columns), skip.
    cols = con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'photos'"
    ).fetchall()
    colset = {c[0] for c in cols}
    if not {"Model", "LensModel"}.issubset(colset):
        pytest.skip("photos view lacks Model/LensModel; rescan photos to include EXIF tags")

    sql = (
        "SELECT Model, LensModel, COUNT(*) AS n "
        "FROM photos GROUP BY 1,2 ORDER BY n DESC LIMIT 25;"
    )
    rows = con.execute(sql).fetchall()

    # Basic shape assertions
    assert isinstance(rows, list)
    # zero rows is acceptable for datasets without EXIF camera/lens tags
    if rows:
        # Each row should have 3 columns: Model, LensModel, n
        assert all(len(r) == 3 for r in rows)
        # Counts should be non-increasing
        counts = [int(r[2]) for r in rows]
        assert counts == sorted(counts, reverse=True)
