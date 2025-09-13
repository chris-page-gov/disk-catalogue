# v0.1.2 — Orchestrated scanning, richer views, and history

## Added
- Orchestrator: `scripts/scan_and_ingest.py` (manifest validation, optional `--update-manifest`).
- All-files scan: `scripts/container_scan_files.sh` (no filters).
- List-based extraction: `scripts/container_extract_photos_from_list.sh`, `scripts/container_extract_videos_from_list.sh`.
- Ingestion upgrades (`scripts/load_csvs.py`): CSV-derived schemas, column alignment, derived views `files`/`photos`/`videos` with `Drive`, `RelativePath`, `RelativeDirectory`, `FileExt`, `FileKey`.
- Drive snapshot table: `drives`; history table: `drive_scans` (start/end, status, CSVs, row counts).
- Manifest template + ignore (`drive_manifest.template.csv`; `drive_manifest.csv` gitignored) and helper `scripts/make_manifest.py`.
- DuckDB CLI in devcontainer (arch-aware); read-only external volume mount; pip user install.
- “Duplicates 101” docs and scan summary queries; scan summary CLI `scripts/scan_summary.py`.

## Changed
- Photo/video scans: capture `FileInode`, `FileCreateDate`, `FileModifyDate`; tolerate non-fatal ExifTool warnings (`-m`).
- Orchestrator closes DB before child processes to avoid file locks.
