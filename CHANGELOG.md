# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]

- (no changes yet)

## [0.1.4] - 2025-09-14

### Added

- Docs: README note about virtualization/Spotlight holding files after scans and mitigation steps.
- Host-run support: `scan_and_ingest.py` auto-detects environment and avoids remapping `/Volumes` when not in the dev container.
- Dev tooling: `scripts/lint.sh --fix` adds auto-fix mode (ruff --fix, ruff format, black).

### Changed

- Git ignore: ignore entire `output/` directory (all generated files, e.g. lists), not just CSV/Parquet.
- Git ignore: ignore `drive_manifest.csv`, `drives_manifest.csv`, and other `drive_manifest*.csv` variants (keep `drive_manifest.template.csv` tracked).

### Fixed

- Ingestion: force DuckDB CSV quoting and dialect to correctly parse paths with commas (e.g., directories like `Locations, Angles`) and avoid type-conversion errors on `FileSize#`.

## [0.1.3] - 2025-09-13

### Added

- CI workflow: lint (Ruff), format checks (Ruff/Black), mypy, and pytest on push/PR.
- CI coverage reporting: generates `coverage.xml` and uploads as artifact.

## [0.1.2] - 2025-09-13

### Added

- Orchestrated scan + ingest command: `scripts/scan_and_ingest.py`.
- Baseline all-files scan: `scripts/container_scan_files.sh` (now scans all files, no filters).
- Targeted extract from lists for efficiency:
  - `scripts/container_extract_photos_from_list.sh`
  - `scripts/container_extract_videos_from_list.sh`
- Ingestion improvements (`scripts/load_csvs.py`):
  - Auto-derive table schema from CSV, align columns on change.
  - Create derived views `files`, `photos`, `videos` with `Drive`, `RelativePath`,
    `RelativeDirectory`, `FileExt`, `FileKey` (stable per-file ID).
- Drive metadata snapshot table `drives` (label, mount, UUID, serial, notes, last_scanned).
- Devcontainer updates:
  - Read-only bind for external volumes (`/Volumes -> /host/Volumes,readonly`).
  - Install deps with `pip install --user -e .[dev]`.
  - DuckDB CLI installed from official release (arch-aware).
- Git: ignore nested `output/**/{csv,parquet}`.
- Manifest: add `drive_manifest.template.csv` and ignore `drive_manifest.csv` in Git.
- Helper: `scripts/make_manifest.py` to bootstrap `drive_manifest.csv` from mounted volumes.
- Orchestrator: `scan_and_ingest.py` validates drive label against manifest; optional `--update-manifest` auto-adds mounted volumes then retries.
- History: `drive_scans` table records each run (start/end, status, CSVs, row counts).
- Utility: `scripts/scan_summary.py` prints last-scan summaries per drive (table/CSV).
- Documentation: “Duplicates 101” examples added to README.md, README_cataloguing.md,
  and sample_queries.sql.
- Documentation: Added scan summary queries (last run, deltas, throughput) to sample_queries.sql and README.

### Changed

- Photo/video scan scripts now capture `FileInode`, `FileCreateDate`, `FileModifyDate` and
  tolerate minor ExifTool warnings (`-m`), only failing on fatal errors.
- `scan_and_ingest.py` closes DB before spawning child processes (avoids DuckDB lock).

## [0.1.1] - 2025-09-12

### Added

- Release after Unreleased changes.

 - 2025-09-06

### Initial Release

- Initial release placeholder.
