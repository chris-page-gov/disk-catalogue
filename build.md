# Cataloguing External Drives

## Prompt

You have multiple mostly-offline spinning drives (5–20 TB each) and want fast discovery of photos, videos, and misc assets without keeping all drives mounted. You also want to keep creative tools (Capture One, DaVinci Resolve) efficient by separating editing workflows from global search/dedupe.

### Plan Overview

1. Scan each drive to CSV (fast, low‑IO metadata extraction using ExifTool / MediaInfo).
2. Ingest CSVs into DuckDB on SSD for fast cross-drive queries.
3. Maintain referenced creative catalogues (Capture One / Resolve) separately.
4. Add checksum + enrichment only when needed (I/O intensive) as a later pass.

### Facts

- Capture One referenced catalogues + large previews allow offline browsing.
- ExifTool (fast mode) + MediaInfo give robust metadata quickly.
- DuckDB comfortably handles millions of rows on local SSD.
- Full cryptographic hashing is accurate but slow on HDDs; defer until necessary.

### Recommended Architecture

- Master index (all drives) in DuckDB for search, dedupe heuristics, reporting.
- Per-tool creative catalogues for editing performance.
- Idempotent ingestion tracked via an `ingested_files` table to avoid re-loading unchanged CSVs.

### Starter Kit (Current Repo)

- `README_cataloguing.md`
- `drive_manifest.csv`
- `duckdb_schema.sql`
- `sample_queries.sql`
- Scan scripts (container versions): `scripts/container_scan_photos.sh`, `scripts/container_scan_videos.sh`
- Ingestion helper: `scripts/load_csvs.py`
- Checksum placeholder: `scripts/enrich_checksums.sh`

### Basic Workflow

1. Label drives and populate `drive_manifest.csv`.
2. Run scan scripts per drive (produces dated CSVs in `output/`).
3. Run the ingestion script (loads new CSVs into DuckDB, logs them).
4. Query via `duckdb` CLI or Python.
5. (Optional later) Run checksum enrichment and advanced dedupe queries.

### Practical Notes

- Store drive label + relative path for portability across OS mount points.
- Start with size/name heuristics before heavy hashing.
- Extend schema gradually (dimensions for camera/lens, checksum tables, etc.).
- Keep DuckDB + Capture One catalogue on SSD; archive CSVs if space grows large.

---

## Development Environment (Container Summary)

The dev container includes: ExifTool, MediaInfo, Python 3.11, uv, DuckDB (Python), Ruff, Black, mypy, pytest. External drives are mounted read-only via `/host/Volumes` (bind from `/Volumes`).

---

## Workflow Outline

1. Install (or open container including) ExifTool, MediaInfo, DuckDB.
2. Populate `drive_manifest.csv` with labels + identifiers.
3. Run scan scripts for each drive (produce dated CSVs per media type).
4. Initialize DuckDB and load/query CSV data.
5. Configure Capture One (referenced, large previews) and gradually ingest historical years.
6. (Later) Add checksum enrichment for duplicate validation.

## Practical Guidelines

- Store drive label + relative path for portability (Mac vs PC mount differences).
- Start with heuristics (size + name) before hashing.
- Extend schema for misc files or hashes incrementally.

## Potential Future Enhancements

- Checksum enrichment pass (+ MD5 / SHA256) and dedupe reporting.
- Misc-file scanner (non-media files).
- Lightweight local web UI for browsing DuckDB results.

## Current Alignment Status

Implemented:

- Dev container with ExifTool, MediaInfo, uv, Python toolchain.
- Scan + ingestion scripts, output folder tracking.
- Initial Python package + tests, lint/type tooling.
- Checksum placeholder script.

## Recommended Next Technical Steps

1. Schema hardening:
   - Replace implicit `read_csv_auto LIMIT 0` staging table creation with explicit `CREATE TABLE` statements (stable types, nullability, constraints).
   - Add ingestion metadata columns (e.g., `ingest_batch_id UUID`, `ingested_at TIMESTAMP DEFAULT now()`), plus `source_filename`.
2. Incremental ingestion:
   - Ensure `scripts/load_csvs.py` writes a batch record and only loads new/changed CSVs (hash the file or store size+mtime for change detection).
3. Checksums phase (optional performance window):
   - Create a `file_checksums` table keyed by stable file identifier (drive_label + relative_path + size) with `md5`, optionally `sha256`, and `computed_at`.
   - Populate gradually (prioritize candidates of suspected duplicates).
4. Normalized dimensions (only if query patterns justify):
   - `dim_camera(body_model)`, `dim_lens(lens_model)`, `dim_drive(drive_label, serial)`. Reference by surrogate keys to reduce repetition.
5. Derived/materialized tables:
   - Materialize frequently queried views (e.g., monthly photo counts, duplicate candidate sets) into tables refreshed after each ingest for faster UI/report latency.
6. Data quality safeguards:
   - Add NOT NULL where safe (e.g., size, modification time, drive_label).
   - Add a uniqueness index on (drive_label, relative_path, size) to guard against accidental double ingestion.
7. Performance & maintenance:
   - Periodic `VACUUM` / `CHECKPOINT` (DuckDB auto-manages, but schedule if DB grows large after deletes/updates).
8. Testing & CI:
   - Add unit tests for ingestion idempotency and duplicate detection logic.
   - GitHub Actions workflow: lint + mypy + pytest + (optional) duckdb SQL smoke test.
9. Future UX:
   - Small CLI (e.g., `diskcat ingest`, `diskcat duplicates`, `diskcat stats`).
   - Optional lightweight web UI (FastAPI + static JS) for browsing.

## Optional Future Enhancements

- True checksum-driven duplicate resolution with prioritization heuristics.
- Misc-file scanner expansion using a generic file walker (reuse Python scanner for non-media types).
- Export/report commands (CSV / HTML summary by drive/year).

## Notes

This document was cleaned to remove duplicated earlier conversation blocks and all hard tab characters; list formatting and headings normalized for readability and lint compliance.
