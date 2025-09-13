# Disk Catalogue

Version: 0.1.2


Early-stage toolkit for scanning mounted volumes and exploring metadata (paths, sizes) via DuckDB.

## Quick Start (Dev Container)

1. Open repository in VS Code.
2. Reopen in container when prompted.
3. (Optional) Install dependencies editable: `uv pip install -e .[dev]` or `pip install -e .[dev]`.
4. Run tests: `pytest`.
5. Format & lint: `ruff check . && ruff format .` (or `black .`).

## Catalogue A Drive

1. Ensure the drive is visible in the container: `ls /host/Volumes/Ext-10`.
2. Create a local manifest (untracked):
   - Copy `drive_manifest.template.csv` to `drive_manifest.csv` and fill values (label, mounts, optional UUID/serial).
   - Note: `drive_manifest.csv` is gitignored to avoid committing machine-specific data.
   - Or bootstrap entries from mounted volumes inside the Dev Container:
     ```bash
     python scripts/make_manifest.py
     ```
3. Run the one-shot scan + ingest:

```bash
python scripts/scan_and_ingest.py --drive Ext-10
```

This writes CSVs under `output/Ext-10/` and ingests them into DuckDB. Re-run later; it skips
already ingested tables for that drive. Use `--force` to rescan.

Tip: If the drive label isn’t in your manifest yet, add `--update-manifest`:

```bash
python scripts/scan_and_ingest.py --drive Ext-10 --update-manifest
```

## Views & Identifiers

- Ingestion creates views `files`, `photos`, `videos` with derived columns:
  - `Drive`, `RelativePath`, `RelativeDirectory`, `FileExt`.
  - `FileKey = hash(Drive, RelativePath, FileSize#)` (stable per-file ID on a drive).
- Example:

```bash
duckdb catalogue.duckdb -c "select Drive, RelativePath, FileExt, \"FileSize#\" from files limit 10;"
```

## Duplicates 101

- By size only (broad candidates):
```bash
duckdb catalogue.duckdb -c "select \"FileSize#\" bytes, count(*) n, count(distinct Drive) drives from files group by 1 having n>1 order by n desc, bytes desc limit 50;"
```
- By name + size (stronger):
```bash
duckdb catalogue.duckdb -c "select lower(FileName) name, \"FileSize#\" bytes, count(*) n, list(distinct Drive) drives from files group by 1,2 having n>1 order by n desc, bytes desc limit 50;"
```
- Pairs across drives (same name + size):
```bash
duckdb catalogue.duckdb -c "select a.Drive a_drive, b.Drive b_drive, a.RelativePath a_path, b.RelativePath b_path, a.\"FileSize#\" bytes from files a join files b on a.\"FileSize#\"=b.\"FileSize#\" and lower(a.FileName)=lower(b.FileName) and a.Drive<b.Drive limit 50;"
```
- Exact match later: add a `file_checksums` table with content hashes (MD5/SHA256) keyed by (Drive, RelativePath, FileSize#), then group by checksum to confirm duplicates precisely.

## Scan Summaries

- Last scan per drive (status + counts): see `sample_queries.sql` section “Scan summaries”.
- Quick run:
```bash
duckdb catalogue.duckdb -c "WITH r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY drive_label ORDER BY started_at DESC) rn FROM drive_scans) SELECT drive_label, started_at, ended_at, status, files_rows, photos_rows, videos_rows, (epoch(ended_at) - epoch(started_at)) AS duration_s FROM r WHERE rn=1 ORDER BY drive_label;"
```
- Or via a friendly CLI table:
```bash
python scripts/scan_summary.py --db catalogue.duckdb
# CSV output:
python scripts/scan_summary.py --db catalogue.duckdb --csv > last_scans.csv
```

## Features (initial)

- Recursive file scanning
- Returns structured `FileRecord` objects
- TDD scaffold (pytest, coverage, mypy, ruff, black)

## Roadmap

See `CHANGELOG.md` and `COPILOT_INSTRUCTIONS.md` for future ideas.

## License

MIT
